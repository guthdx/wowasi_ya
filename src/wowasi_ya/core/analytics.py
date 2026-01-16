"""
Analytics module for Wowasi_ya.
Provides SQLite-based usage tracking and metrics.
"""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

# Database file path
DB_PATH = Path(__file__).parent.parent.parent.parent / "analytics.db"

# Claude API pricing (per 1M tokens) - Sonnet 4
CLAUDE_INPUT_COST = 3.00  # $3.00 per 1M input tokens
CLAUDE_OUTPUT_COST = 15.00  # $15.00 per 1M output tokens


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Initialize the database with required tables."""
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS project_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT UNIQUE NOT NULL,
                timestamp TEXT NOT NULL,

                -- Request metadata
                ip_address TEXT,
                user_agent TEXT,

                -- Project info
                project_name TEXT,
                description_length INTEGER,
                privacy_flags_count INTEGER DEFAULT 0,
                domains_identified INTEGER DEFAULT 0,
                agents_generated INTEGER DEFAULT 0,

                -- Processing status
                status TEXT NOT NULL DEFAULT 'pending',
                error_message TEXT,
                current_phase TEXT,

                -- Phase timing (seconds)
                total_duration REAL,
                phase_discovery_duration REAL,
                phase_research_duration REAL,
                phase_generation_duration REAL,
                phase_quality_duration REAL,
                phase_output_duration REAL,

                -- Generation batch timing (seconds)
                batch1_duration REAL,
                batch2_duration REAL,
                batch3_duration REAL,
                batch4_duration REAL,
                batch5_duration REAL,

                -- Token usage (research phase - Claude)
                research_prompt_tokens INTEGER DEFAULT 0,
                research_completion_tokens INTEGER DEFAULT 0,
                research_total_tokens INTEGER DEFAULT 0,

                -- Token usage (generation phase - may be Claude or Llama)
                generation_prompt_tokens INTEGER DEFAULT 0,
                generation_completion_tokens INTEGER DEFAULT 0,
                generation_total_tokens INTEGER DEFAULT 0,
                generation_provider TEXT,

                -- Cost estimation (USD)
                research_cost_usd REAL DEFAULT 0.0,
                generation_cost_usd REAL DEFAULT 0.0,
                total_cost_usd REAL DEFAULT 0.0,

                -- Results
                documents_generated INTEGER DEFAULT 0,
                total_words_generated INTEGER DEFAULT 0,
                quality_score REAL,

                -- Output destinations
                output_filesystem INTEGER DEFAULT 0,
                output_obsidian INTEGER DEFAULT 0,
                output_git INTEGER DEFAULT 0,
                output_gdrive INTEGER DEFAULT 0,
                output_outline INTEGER DEFAULT 0,

                -- Paths
                output_directory TEXT,
                outline_collection_id TEXT
            )
        ''')

        # Create indexes for common queries
        conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON project_logs(timestamp)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_status ON project_logs(status)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_ip_address ON project_logs(ip_address)')

        conn.commit()


def log_project_start(
    project_id: str,
    project_name: str,
    description_length: int,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    """Log the start of a new project."""
    with get_db_connection() as conn:
        conn.execute('''
            INSERT INTO project_logs (
                project_id, timestamp, ip_address, user_agent,
                project_name, description_length, status, current_phase
            ) VALUES (?, ?, ?, ?, ?, ?, 'processing', 'discovery')
        ''', (
            project_id,
            datetime.utcnow().isoformat(),
            ip_address,
            user_agent,
            project_name,
            description_length,
        ))
        conn.commit()


def update_discovery_results(
    project_id: str,
    domains_count: int,
    agents_count: int,
    privacy_flags_count: int,
    duration: float,
) -> None:
    """Update discovery phase results."""
    with get_db_connection() as conn:
        conn.execute('''
            UPDATE project_logs SET
                domains_identified = ?,
                agents_generated = ?,
                privacy_flags_count = ?,
                phase_discovery_duration = ?,
                current_phase = 'research'
            WHERE project_id = ?
        ''', (domains_count, agents_count, privacy_flags_count, duration, project_id))
        conn.commit()


def log_research_complete(
    project_id: str,
    duration: float,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
) -> None:
    """Log research phase completion with token usage."""
    total_tokens = prompt_tokens + completion_tokens

    # Calculate cost (Claude API)
    input_cost = (prompt_tokens / 1_000_000) * CLAUDE_INPUT_COST
    output_cost = (completion_tokens / 1_000_000) * CLAUDE_OUTPUT_COST
    research_cost = input_cost + output_cost

    with get_db_connection() as conn:
        conn.execute('''
            UPDATE project_logs SET
                phase_research_duration = ?,
                research_prompt_tokens = ?,
                research_completion_tokens = ?,
                research_total_tokens = ?,
                research_cost_usd = ?,
                current_phase = 'generation'
            WHERE project_id = ?
        ''', (duration, prompt_tokens, completion_tokens, total_tokens, research_cost, project_id))
        conn.commit()


def log_batch_complete(
    project_id: str,
    batch_number: int,
    duration: float,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    provider: str = "claude",
) -> None:
    """Log completion of a generation batch."""
    batch_column = f"batch{batch_number}_duration"

    with get_db_connection() as conn:
        # Update batch duration
        conn.execute(f'''
            UPDATE project_logs SET
                {batch_column} = ?,
                generation_prompt_tokens = generation_prompt_tokens + ?,
                generation_completion_tokens = generation_completion_tokens + ?,
                generation_total_tokens = generation_total_tokens + ?,
                generation_provider = ?
            WHERE project_id = ?
        ''', (duration, prompt_tokens, completion_tokens, prompt_tokens + completion_tokens, provider, project_id))
        conn.commit()


def log_generation_complete(
    project_id: str,
    total_duration: float,
    documents_count: int,
    total_words: int,
    provider: str = "claude",
) -> None:
    """Log generation phase completion."""
    with get_db_connection() as conn:
        # Get current token counts to calculate generation cost
        row = conn.execute(
            'SELECT generation_prompt_tokens, generation_completion_tokens FROM project_logs WHERE project_id = ?',
            (project_id,)
        ).fetchone()

        generation_cost = 0.0
        if row and provider == "claude":
            prompt_tokens = row['generation_prompt_tokens'] or 0
            completion_tokens = row['generation_completion_tokens'] or 0
            input_cost = (prompt_tokens / 1_000_000) * CLAUDE_INPUT_COST
            output_cost = (completion_tokens / 1_000_000) * CLAUDE_OUTPUT_COST
            generation_cost = input_cost + output_cost
        # Llama is free (local inference)

        conn.execute('''
            UPDATE project_logs SET
                phase_generation_duration = ?,
                documents_generated = ?,
                total_words_generated = ?,
                generation_cost_usd = ?,
                current_phase = 'quality'
            WHERE project_id = ?
        ''', (total_duration, documents_count, total_words, generation_cost, project_id))
        conn.commit()


def log_quality_complete(
    project_id: str,
    duration: float,
    quality_score: float | None = None,
) -> None:
    """Log quality check phase completion."""
    with get_db_connection() as conn:
        conn.execute('''
            UPDATE project_logs SET
                phase_quality_duration = ?,
                quality_score = ?,
                current_phase = 'output'
            WHERE project_id = ?
        ''', (duration, quality_score, project_id))
        conn.commit()


def log_output_complete(
    project_id: str,
    duration: float,
    filesystem: bool = False,
    obsidian: bool = False,
    git: bool = False,
    gdrive: bool = False,
    outline: bool = False,
    output_directory: str | None = None,
    outline_collection_id: str | None = None,
) -> None:
    """Log output phase completion."""
    with get_db_connection() as conn:
        conn.execute('''
            UPDATE project_logs SET
                phase_output_duration = ?,
                output_filesystem = ?,
                output_obsidian = ?,
                output_git = ?,
                output_gdrive = ?,
                output_outline = ?,
                output_directory = ?,
                outline_collection_id = ?
            WHERE project_id = ?
        ''', (
            duration,
            1 if filesystem else 0,
            1 if obsidian else 0,
            1 if git else 0,
            1 if gdrive else 0,
            1 if outline else 0,
            output_directory,
            outline_collection_id,
            project_id,
        ))
        conn.commit()


def log_project_complete(
    project_id: str,
    status: str = "success",
    total_duration: float | None = None,
    error_message: str | None = None,
) -> None:
    """Log project completion with final metrics."""
    with get_db_connection() as conn:
        # Calculate total cost
        row = conn.execute(
            'SELECT research_cost_usd, generation_cost_usd FROM project_logs WHERE project_id = ?',
            (project_id,)
        ).fetchone()

        total_cost = 0.0
        if row:
            total_cost = (row['research_cost_usd'] or 0) + (row['generation_cost_usd'] or 0)

        conn.execute('''
            UPDATE project_logs SET
                status = ?,
                total_duration = ?,
                total_cost_usd = ?,
                error_message = ?,
                current_phase = NULL
            WHERE project_id = ?
        ''', (status, total_duration, total_cost, error_message, project_id))
        conn.commit()


def log_project_error(
    project_id: str,
    error_message: str,
    phase: str | None = None,
) -> None:
    """Log a project error."""
    with get_db_connection() as conn:
        conn.execute('''
            UPDATE project_logs SET
                status = 'failed',
                error_message = ?,
                current_phase = ?
            WHERE project_id = ?
        ''', (error_message, phase, project_id))
        conn.commit()


def get_analytics_summary() -> dict:
    """Get aggregated analytics summary."""
    with get_db_connection() as conn:
        # Total projects
        total = conn.execute('SELECT COUNT(*) as count FROM project_logs').fetchone()['count']

        # Status counts
        success = conn.execute(
            "SELECT COUNT(*) as count FROM project_logs WHERE status = 'success'"
        ).fetchone()['count']

        failed = conn.execute(
            "SELECT COUNT(*) as count FROM project_logs WHERE status = 'failed'"
        ).fetchone()['count']

        processing = conn.execute(
            "SELECT COUNT(*) as count FROM project_logs WHERE status = 'processing'"
        ).fetchone()['count']

        # Average duration (completed projects only)
        avg_duration = conn.execute('''
            SELECT AVG(total_duration) as avg_duration
            FROM project_logs
            WHERE status = 'success' AND total_duration IS NOT NULL
        ''').fetchone()['avg_duration']

        # Total cost
        total_cost = conn.execute(
            'SELECT SUM(total_cost_usd) as total FROM project_logs'
        ).fetchone()['total'] or 0.0

        # Total tokens
        total_research_tokens = conn.execute(
            'SELECT SUM(research_total_tokens) as total FROM project_logs'
        ).fetchone()['total'] or 0

        total_generation_tokens = conn.execute(
            'SELECT SUM(generation_total_tokens) as total FROM project_logs'
        ).fetchone()['total'] or 0

        # Total documents and words
        total_documents = conn.execute(
            'SELECT SUM(documents_generated) as total FROM project_logs'
        ).fetchone()['total'] or 0

        total_words = conn.execute(
            'SELECT SUM(total_words_generated) as total FROM project_logs'
        ).fetchone()['total'] or 0

        # Output destination counts
        output_counts = conn.execute('''
            SELECT
                SUM(output_filesystem) as filesystem,
                SUM(output_obsidian) as obsidian,
                SUM(output_git) as git,
                SUM(output_gdrive) as gdrive,
                SUM(output_outline) as outline
            FROM project_logs
        ''').fetchone()

        # Provider usage
        claude_count = conn.execute(
            "SELECT COUNT(*) as count FROM project_logs WHERE generation_provider = 'claude'"
        ).fetchone()['count']

        llama_count = conn.execute(
            "SELECT COUNT(*) as count FROM project_logs WHERE generation_provider = 'llamacpp'"
        ).fetchone()['count']

        # Unique IPs
        unique_ips = conn.execute(
            'SELECT COUNT(DISTINCT ip_address) as count FROM project_logs WHERE ip_address IS NOT NULL'
        ).fetchone()['count']

        # Projects per day (last 30 days)
        thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
        daily_counts = conn.execute('''
            SELECT DATE(timestamp) as date, COUNT(*) as count
            FROM project_logs
            WHERE timestamp >= ?
            GROUP BY DATE(timestamp)
            ORDER BY date
        ''', (thirty_days_ago,)).fetchall()

        # Average phase durations
        phase_avgs = conn.execute('''
            SELECT
                AVG(phase_discovery_duration) as discovery,
                AVG(phase_research_duration) as research,
                AVG(phase_generation_duration) as generation,
                AVG(phase_quality_duration) as quality,
                AVG(phase_output_duration) as output
            FROM project_logs
            WHERE status = 'success'
        ''').fetchone()

        # Average quality score
        avg_quality = conn.execute('''
            SELECT AVG(quality_score) as avg_score
            FROM project_logs
            WHERE status = 'success' AND quality_score IS NOT NULL
        ''').fetchone()['avg_score']

        return {
            'total_projects': total,
            'success_count': success,
            'failed_count': failed,
            'processing_count': processing,
            'success_rate': round((success / total) * 100, 1) if total > 0 else 0,
            'avg_duration_seconds': round(avg_duration, 2) if avg_duration else None,
            'total_cost_usd': round(total_cost, 4),
            'total_research_tokens': total_research_tokens,
            'total_generation_tokens': total_generation_tokens,
            'total_tokens': total_research_tokens + total_generation_tokens,
            'total_documents_generated': total_documents,
            'total_words_generated': total_words,
            'avg_quality_score': round(avg_quality, 2) if avg_quality else None,
            'output_destinations': {
                'filesystem': output_counts['filesystem'] or 0,
                'obsidian': output_counts['obsidian'] or 0,
                'git': output_counts['git'] or 0,
                'gdrive': output_counts['gdrive'] or 0,
                'outline': output_counts['outline'] or 0,
            },
            'provider_usage': {
                'claude': claude_count,
                'llamacpp': llama_count,
            },
            'unique_ips': unique_ips,
            'daily_counts': [{'date': row['date'], 'count': row['count']} for row in daily_counts],
            'avg_phase_durations': {
                'discovery': round(phase_avgs['discovery'], 2) if phase_avgs['discovery'] else None,
                'research': round(phase_avgs['research'], 2) if phase_avgs['research'] else None,
                'generation': round(phase_avgs['generation'], 2) if phase_avgs['generation'] else None,
                'quality': round(phase_avgs['quality'], 2) if phase_avgs['quality'] else None,
                'output': round(phase_avgs['output'], 2) if phase_avgs['output'] else None,
            },
        }


def get_recent_projects(limit: int = 50) -> list[dict]:
    """Get recent projects for the dashboard."""
    with get_db_connection() as conn:
        rows = conn.execute('''
            SELECT
                project_id, timestamp, project_name, status,
                total_duration, total_cost_usd, documents_generated,
                total_words_generated, generation_provider, error_message
            FROM project_logs
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,)).fetchall()

        return [dict(row) for row in rows]


def get_project_details(project_id: str) -> dict | None:
    """Get full details for a single project."""
    with get_db_connection() as conn:
        row = conn.execute(
            'SELECT * FROM project_logs WHERE project_id = ?',
            (project_id,)
        ).fetchone()

        if row:
            return dict(row)
        return None


def check_db_health() -> bool:
    """Check if the database is accessible and healthy."""
    try:
        with get_db_connection() as conn:
            conn.execute('SELECT 1').fetchone()
            return True
    except Exception:
        return False


# Initialize database on module import
init_db()
