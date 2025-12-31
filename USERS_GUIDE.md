# Wowasi Ya User Guide

**Wowasi Ya** (Lakota: "Assistant") is an AI-powered project documentation generator that creates 15 standardized project documents from a simple description.

---

## Table of Contents

1. [Overview](#overview)
2. [What You Get](#what-you-get)
3. [Available Tools](#available-tools)
4. [Complete Workflow](#complete-workflow)
5. [Using the CLI](#using-the-cli)
6. [Using the API](#using-the-api)
7. [Using the Portal](#using-the-portal)
8. [Working with Next Steps](#working-with-next-steps)
9. [Troubleshooting](#troubleshooting)

---

## Overview

Wowasi Ya transforms a brief project description into comprehensive documentation. Instead of spending hours writing project briefs, risk assessments, and timelines, you provide a description and the system generates professional-grade documents using AI research and generation.

### How It Works

```
Your Project Description
         |
         v
Phase 0: Agent Discovery (identifies relevant domains)
         |
         v
Phase 1: Privacy Review (scans for sensitive data)
         |
         v
Phase 2: Research (AI searches for relevant information)
         |
         v
Phase 3: Document Generation (creates 15 documents)
         |
         v
Phase 4: Quality Check (validates completeness)
         |
         v
Phase 5: Output (files, Outline Wiki, or both)
```

---

## What You Get

Wowasi Ya generates **15 standardized project documents** organized into 5 phases:

### Phase 1: Foundation
| Document | Purpose |
|----------|---------|
| Project Brief | Executive summary and project overview |
| README | Quick reference for the project |
| Glossary | Key terms and definitions |

### Phase 2: Discovery
| Document | Purpose |
|----------|---------|
| Context & Background | Industry context and environment |
| Stakeholder Notes | Key people and their interests |

### Phase 3: Planning
| Document | Purpose |
|----------|---------|
| Goals & Success Criteria | Measurable objectives and KPIs |
| Scope & Boundaries | What's in and out of scope |
| Timeline & Milestones | Project schedule with key dates |
| Initial Budget | Cost estimates and resource needs |
| Risks & Assumptions | Potential issues and mitigation |

### Phase 4: Execution
| Document | Purpose |
|----------|---------|
| Process Workflow | Step-by-step process diagrams |
| SOPs | Standard operating procedures |
| Task Backlog | Prioritized work items |

### Phase 5: Tracking
| Document | Purpose |
|----------|---------|
| Status Updates | Progress reporting template |
| Meeting Notes | Meeting documentation template |

---

## Available Tools

### 1. Command Line Interface (CLI)

Best for: Developers, automation, scripting

```bash
wowasi generate "Project Name" "Description..."
```

### 2. REST API

Best for: Integration with other systems, programmatic access

```bash
curl -X POST https://wowasi.iyeska.net/api/v1/projects \
  -u admin:password \
  -H "Content-Type: application/json" \
  -d '{"name": "Project Name", "description": "Description..."}'
```

### 3. Web Portal

Best for: Non-technical users, progress tracking, team collaboration

Access at: https://portal.iyeska.net (coming soon)

---

## Complete Workflow

This section walks through the full process from start to finish.

### Step 1: Create a Project

You can create a project using either the CLI or API.

#### Using the CLI

```bash
# Basic usage
wowasi generate "Employee Onboarding System" \
  "A web-based system to streamline the onboarding process for new employees,
   including document management, training schedules, and manager approvals."

# With additional context
wowasi generate "Employee Onboarding System" \
  "A web-based system to streamline the onboarding process..." \
  --context "This is for a healthcare organization with 500 employees"
```

#### Using the API

```bash
# Step 1: Create the project
curl -X POST https://wowasi.iyeska.net/api/v1/projects \
  -u admin:password \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Employee Onboarding System",
    "description": "A web-based system to streamline the onboarding process for new employees, including document management, training schedules, and manager approvals.",
    "additional_context": "Healthcare organization with 500 employees"
  }'

# Response:
# {
#   "project_id": "abc123-...",
#   "status": "agent_discovery",
#   "message": "Project created. Use GET /projects/{id}/discovery to see results."
# }
```

### Step 2: Review Privacy Flags

Before any API calls are made, the system scans your input for sensitive information (names, emails, phone numbers, SSNs, etc.).

#### CLI Behavior

The CLI automatically prompts you:

```
Found 2 potential sensitive items:

  - EMAIL: john.smith@company.com
  - PERSON: John Smith

Proceed with sanitized text? [Y/n]:
```

Type `Y` to continue with placeholders replacing sensitive data.

#### API Behavior

```bash
# Get discovery and privacy results
curl -X GET https://wowasi.iyeska.net/api/v1/projects/abc123/discovery \
  -u admin:password

# Review the privacy_scan section in the response
# Then approve:
curl -X POST https://wowasi.iyeska.net/api/v1/projects/abc123/approve \
  -u admin:password \
  -H "Content-Type: application/json" \
  -d '{"approved": true, "use_sanitized": true}'
```

### Step 3: Wait for Generation

Document generation typically takes **3-8 minutes** depending on:
- Number of research agents activated
- Llama server availability (falls back to Claude if unavailable)
- Network conditions

#### CLI

The CLI shows progress in real-time:

```
Phase 0: Discovering agents... done
Phase 1: Researching... done
Phase 2: Generating documents... done
Phase 3: Quality check... done
Phase 4: Writing output... done

Generation complete!

Output written to:
  - ./output/Employee_Onboarding_System/01_project_brief.md
  - ./output/Employee_Onboarding_System/02_readme.md
  - ... and 13 more files
```

#### API

Poll the status endpoint:

```bash
curl -X GET https://wowasi.iyeska.net/api/v1/projects/abc123/status \
  -u admin:password

# Response shows progress:
# {"project_id": "abc123", "status": "generating", "phase": 2, "documents_generated": 8}
```

### Step 4: Publish to Outline Wiki

Once generation completes, publish to Outline for easy viewing and collaboration.

```bash
curl -X POST https://wowasi.iyeska.net/api/v1/projects/abc123/publish-to-outline \
  -u admin:password \
  -H "Content-Type: application/json" \
  -d '{"enable_sharing": true}'

# Response:
# {
#   "collection_url": "https://docs.iyeska.net/collection/employee-onboarding",
#   "public_url": "https://docs.iyeska.net/s/abc123",
#   "document_urls": ["https://docs.iyeska.net/doc/...", ...],
#   "message": "Successfully published 15 documents to Outline"
# }
```

**Options:**
- `enable_sharing: true` - Creates a public link anyone can access (no login required)
- `enable_sharing: false` - Documents are private to authenticated Outline users

### Step 5: Create Next Steps

After publishing, create actionable next steps for the project:

```bash
curl -X POST https://wowasi.iyeska.net/api/v1/projects/abc123/next-steps \
  -u admin:password \
  -H "Content-Type: application/json" \
  -d '{}'

# Response:
# {"project_id": "abc123", "steps_created": 37, "message": "Created 37 next steps for project"}
```

### Step 6: Track Progress

View and update next steps as your team works through them:

```bash
# Get all next steps
curl -X GET https://wowasi.iyeska.net/api/v1/projects/abc123/next-steps

# Get progress summary
curl -X GET https://wowasi.iyeska.net/api/v1/projects/abc123/progress

# Mark a step complete
curl -X POST https://wowasi.iyeska.net/api/v1/projects/abc123/next-steps/step-123/complete \
  -u admin:password \
  -H "Content-Type: application/json" \
  -d '{"completed_by": "jane@company.com"}'
```

---

## Using the CLI

### Installation

```bash
# Clone the repository
git clone https://github.com/guthdx/wowasi_ya.git
cd wowasi_ya

# Create virtual environment (Python 3.11+ required)
python3 -m venv .venv
source .venv/bin/activate

# Install
pip install -e ".[dev]"

# Set up environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### Available Commands

| Command | Description |
|---------|-------------|
| `wowasi generate` | Generate all 15 documents |
| `wowasi discover` | Run discovery only (no API calls) |
| `wowasi privacy-check` | Scan text for sensitive data |
| `wowasi audit` | View API usage logs |
| `wowasi serve` | Start the API server |
| `wowasi version` | Show version info |

### Generate Command Options

```bash
wowasi generate "Name" "Description" [OPTIONS]

Options:
  --context, -c TEXT     Additional context
  --format, -f TEXT      Output: filesystem, obsidian, git [default: filesystem]
  --output, -o PATH      Custom output directory
  --skip-privacy         Skip privacy review (not recommended)
```

### Examples

```bash
# Basic generation
wowasi generate "Mobile App Redesign" "Redesign our iOS app for better UX"

# With context and custom output
wowasi generate "Data Migration" \
  "Migrate from MySQL to PostgreSQL" \
  --context "Production database with 10TB of data" \
  --output ~/Projects/data-migration/docs

# Output to Obsidian vault
wowasi generate "Research Paper" \
  "Study on remote work productivity" \
  --format obsidian
```

---

## Using the API

### Base URL

- **Local**: http://localhost:8001/api/v1
- **Production**: https://wowasi.iyeska.net/api/v1

### Authentication

Most endpoints require HTTP Basic Authentication:

```bash
curl -u admin:password https://wowasi.iyeska.net/api/v1/projects
```

### Interactive Documentation

Visit `/docs` for Swagger UI:
- http://localhost:8001/docs (local)
- https://wowasi.iyeska.net/docs (production)

### Complete API Flow Example

```bash
# 1. Create project
PROJECT_ID=$(curl -s -X POST https://wowasi.iyeska.net/api/v1/projects \
  -u admin:password \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Project", "description": "A test project description"}' \
  | jq -r '.project_id')

echo "Created project: $PROJECT_ID"

# 2. Get discovery results
curl -s -X GET "https://wowasi.iyeska.net/api/v1/projects/$PROJECT_ID/discovery" \
  -u admin:password | jq '.privacy_scan'

# 3. Approve and start generation
curl -s -X POST "https://wowasi.iyeska.net/api/v1/projects/$PROJECT_ID/approve" \
  -u admin:password \
  -H "Content-Type: application/json" \
  -d '{"approved": true}'

# 4. Poll for completion
while true; do
  STATUS=$(curl -s -X GET "https://wowasi.iyeska.net/api/v1/projects/$PROJECT_ID/status" \
    -u admin:password | jq -r '.status')
  echo "Status: $STATUS"
  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
    break
  fi
  sleep 10
done

# 5. Get results
curl -s -X GET "https://wowasi.iyeska.net/api/v1/projects/$PROJECT_ID/result" \
  -u admin:password | jq '.documents | length'

# 6. Publish to Outline
curl -s -X POST "https://wowasi.iyeska.net/api/v1/projects/$PROJECT_ID/publish-to-outline" \
  -u admin:password \
  -H "Content-Type: application/json" \
  -d '{"enable_sharing": true}' | jq '.public_url'

# 7. Create next steps
curl -s -X POST "https://wowasi.iyeska.net/api/v1/projects/$PROJECT_ID/next-steps" \
  -u admin:password \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## Using the Portal

The web portal provides a visual interface for tracking project progress and completing next steps.

### Accessing the Portal

- **URL**: https://portal.iyeska.net (coming soon)
- **Local Development**: http://portal.localhost

### Dashboard View

The dashboard shows all your projects with:
- Project name and status
- Progress bar (percentage of next steps completed)
- Quick access to documents and next steps

### Project View

Click on a project to see:
- Documents organized by phase (Foundation, Discovery, Planning, Execution, Tracking)
- Overall progress metrics
- Links to view documents in Outline

### Document View

Each document page shows:
- The document content (embedded from Outline)
- Associated next steps for that document
- Actions to mark steps complete or skip them

### Completing Next Steps

Each next step has:
- **Title**: What needs to be done
- **Description**: Detailed instructions
- **Action Type**: Guidance (read-only), Checklist (interactive), or Form (input required)
- **Status**: Not Started, In Progress, Completed, or Skipped

To complete a step:
1. Click on the step card
2. Fill in any required information
3. Click "Mark Complete"

---

## Working with Next Steps

### What Are Next Steps?

Documents alone aren't enough to execute a project. Next Steps are actionable tasks that help you put the documents into practice.

Each document type has predefined next steps. For example:

**Project Brief Next Steps:**
1. Share with stakeholders for feedback
2. Identify gaps or questions
3. Schedule kickoff meeting

**Risks & Assumptions Next Steps:**
1. Assign risk owners
2. Schedule risk review meetings
3. Prioritize mitigation strategies

### Action Types

| Type | Description | Example |
|------|-------------|---------|
| **Guidance** | Read-only instructions | "Review the project brief with your team" |
| **Checklist** | Interactive checkboxes | Items to verify before proceeding |
| **Form** | Input fields | Assign owner, set due date, add notes |

### Progress Tracking

The `/progress` endpoint returns:

```json
{
  "project_id": "abc123",
  "total_steps": 37,
  "completed_steps": 15,
  "skipped_steps": 2,
  "in_progress_steps": 3,
  "not_started_steps": 17,
  "completion_percentage": 40.5,
  "required_steps_remaining": 8
}
```

---

## Troubleshooting

### "Llama Unavailable" Warning

**Symptom**: Health check shows `"llamacpp": {"available": false}`

**Cause**: The M4 Mac running Llama is offline or the Cloudflare tunnel is down.

**Impact**: Generation will use Claude API (more expensive but still works).

**Fix**:
1. Check that the Mac is powered on and connected to internet
2. Verify Llama server is running: `ps aux | grep llama` on Mac
3. Check Cloudflare tunnel: `cloudflared tunnel list`

### Privacy Check Blocking Generation

**Symptom**: Privacy scan detects too many false positives

**Fix**:
1. Use `--skip-privacy` flag (CLI only, not recommended for production)
2. Adjust `PRIVACY_CONFIDENCE_THRESHOLD` in `.env` (default 0.7)
3. Review and sanitize input before submission

### Generation Taking Too Long

**Expected Time**: 3-8 minutes for 15 documents

**If Longer**:
1. Check `/health` endpoint for provider status
2. Review audit logs: `wowasi audit --limit 10`
3. Check network connectivity to API endpoints

### Documents Not Appearing in Outline

**Check**:
1. Verify `OUTLINE_API_KEY` is set in `.env`
2. Ensure Outline is running: visit https://docs.iyeska.net
3. Check API response from `/publish-to-outline` for errors

### API Authentication Failing

**Symptom**: `401 Unauthorized` response

**Fix**:
1. Verify `ADMIN_USERNAME` and `ADMIN_PASSWORD` in `.env`
2. Ensure you're using Basic Auth (not Bearer token)
3. Check credentials aren't URL-encoded incorrectly

### Missing Documents in Output

**Symptom**: Only some documents generated

**Check**:
1. Review `quality_issues` in the result response
2. Check for research errors in audit logs
3. Verify input description is detailed enough

---

## Getting Help

- **API Docs**: https://wowasi.iyeska.net/docs
- **GitHub Issues**: https://github.com/guthdx/wowasi_ya/issues
- **Slack**: #wowasi-support

---

## Quick Reference

### CLI Commands

```bash
wowasi generate "Name" "Description" [--context "..."] [--format filesystem|obsidian|git]
wowasi discover "Name" "Description"
wowasi privacy-check "text to scan"
wowasi audit [--project ID] [--limit 20]
wowasi serve [--host 0.0.0.0] [--port 8000] [--reload]
wowasi version
```

### API Endpoints

```
GET  /health                               # System health (public)
POST /projects                             # Create project (auth required)
GET  /projects                             # List projects (public)
GET  /projects/{id}/discovery              # Get discovery (auth required)
POST /projects/{id}/approve                # Start generation (auth required)
GET  /projects/{id}/status                 # Check progress (auth required)
GET  /projects/{id}/result                 # Get documents (auth required)
POST /projects/{id}/publish-to-outline     # Publish to Outline (auth required)
POST /projects/{id}/next-steps             # Create next steps (auth required)
GET  /projects/{id}/next-steps             # List next steps (public)
GET  /projects/{id}/progress               # Get progress (public)
POST /projects/{id}/next-steps/{id}/complete   # Mark complete (auth required)
POST /projects/{id}/next-steps/{id}/skip       # Skip step (auth required)
```

### Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<secure-password>
SECRET_KEY=<random-key>

# Optional - Outline Integration
OUTLINE_API_KEY=ol_...
OUTLINE_BASE_URL=https://docs.iyeska.net

# Optional - Output
OUTPUT_DIR=./output
ENABLE_GDRIVE_SYNC=false
```
