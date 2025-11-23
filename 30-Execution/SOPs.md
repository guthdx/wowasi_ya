# Standard Operating Procedures

## SOP-001: Generating a New Project

### Purpose
Create a complete set of project documentation from a project description.

### When to Use
When starting any new project that would benefit from structured documentation.

### Roles Involved
- **User:** Provides project description, reviews privacy flags, receives output

### Prerequisites
- Wowasi_ya is running and accessible
- User has valid credentials
- Claude API key is configured and has available credits

### Procedure

1. **Access Wowasi_ya**
   - Web: Navigate to the configured URL
   - CLI: Open terminal, navigate to wowasi_ya directory

2. **Authenticate**
   - Enter username and password
   - Verify successful login

3. **Enter Project Information**
   - Project name (short, descriptive)
   - Project description (be specific - more detail = better output)
   - Optional: known stakeholders, constraints, timeline, budget range

4. **Review Privacy Flags**
   - System will highlight potentially sensitive content
   - For each flagged item:
     - **Approve:** Content is OK to send to API
     - **Modify:** Edit to remove/redact sensitive details
     - **Cancel:** Stop generation if too sensitive

5. **Wait for Generation**
   - Progress indicator shows current phase
   - Typical time: 2-5 minutes depending on complexity

6. **Review Output**
   - Check completion status
   - Review any warnings
   - Access generated documents

7. **Verify Quality**
   - Open key documents (README, Project-Brief, Goals)
   - Confirm content is relevant and accurate
   - Note any needed edits

8. **Export/Use**
   - Documents are automatically saved to configured location
   - Optionally sync to Obsidian or git

---

## SOP-002: Reviewing Privacy Flags

### Purpose
Ensure sensitive information is not inadvertently sent to external APIs.

### When to Use
During every project generation, when privacy layer presents flagged content.

### Roles Involved
- **User:** Reviews and approves/modifies flagged content

### Procedure

1. **Understand Flag Categories**
   - **PHI (Protected Health Information):** Medical conditions, treatment info
   - **PII (Personally Identifiable Information):** Names, SSN, addresses, DOB
   - **Tribal-Specific:** Enrollment info, cultural details, internal governance

2. **Review Each Flag**
   - Read the flagged content in context
   - Ask: "Would I be comfortable if this appeared in a public document?"

3. **Decide Action**
   | Situation | Action |
   |-----------|--------|
   | Content is actually public/generic | Approve |
   | Content has specific names/numbers | Modify to use placeholders |
   | Content is truly sensitive | Modify to generalize or remove |
   | Entire description too sensitive | Cancel and rewrite description |

4. **Modify Content (if needed)**
   - Replace specific names with roles: "John Smith" → "Project Lead"
   - Replace specific numbers: "SSN 123-45-6789" → "[SSN REDACTED]"
   - Generalize locations: "123 Main St, Tribal HQ" → "Tribal administrative facility"

5. **Confirm and Proceed**
   - Verify all flags addressed
   - Click approve/continue
   - Audit log captures your approval

---

## SOP-003: Regenerating Individual Documents

### Purpose
Re-generate specific documents that need improvement without redoing the entire project.

### When to Use
When one or more generated documents are unsatisfactory but others are fine.

### Roles Involved
- **User:** Identifies documents needing regeneration

### Procedure

1. **Identify Problem Documents**
   - Note which specific documents need improvement
   - Identify what's wrong (too generic, missing info, wrong focus)

2. **Access Regeneration Option**
   - Web: Click "Regenerate" button on document view
   - CLI: Use `wowasi_ya regenerate --doc <document-name>`

3. **Provide Additional Guidance (optional)**
   - Add specific instructions for the regeneration
   - Example: "Focus more on USDA compliance requirements"
   - Example: "Include specific stakeholder: Tribal Council"

4. **Review Privacy Flags (if new content)**
   - Any new guidance is scanned
   - Approve/modify as in SOP-002

5. **Wait for Regeneration**
   - Only the specified document is regenerated
   - Uses existing research brief as context

6. **Review Updated Document**
   - Compare to original if helpful
   - Verify improvement
   - Repeat if still unsatisfactory

---

## SOP-004: Configuring Output Destinations

### Purpose
Set up where generated project documents are saved.

### When to Use
Initial setup, or when changing output preferences.

### Roles Involved
- **Admin/User:** Configures output settings

### Procedure

1. **Access Configuration**
   - Web: Settings → Output Destinations
   - CLI: Edit `config.yaml` or use `wowasi_ya config`

2. **Configure Filesystem Output**
   ```yaml
   output:
     filesystem:
       enabled: true
       base_path: /path/to/projects
       create_dated_folder: true
   ```

3. **Configure Obsidian Output (optional)**
   ```yaml
   output:
     obsidian:
       enabled: true
       vault_path: /path/to/obsidian/vault
       folder: Projects
   ```

4. **Configure Git Output (optional)**
   ```yaml
   output:
     git:
       enabled: true
       auto_init: true
       auto_commit: true
       remote: ""  # Leave empty for local only
   ```

5. **Save Configuration**
   - Web: Click Save
   - CLI: Save file, restart if needed

6. **Test Configuration**
   - Generate a test project
   - Verify files appear in expected locations

---

## SOP-005: Reviewing Audit Logs

### Purpose
Review what data has been sent to external APIs.

### When to Use
Periodic review, after sensitive projects, or when investigating issues.

### Roles Involved
- **Admin/User:** Reviews logs

### Procedure

1. **Access Audit Logs**
   - Web: Admin → Audit Logs
   - CLI: `wowasi_ya logs --type api`
   - File: Check `logs/api_audit.log`

2. **Understand Log Format**
   ```
   [timestamp] [project_id] [action] [summary]
   2024-01-15T10:30:00 proj_abc123 API_CALL "Research agent: healthcare-compliance"
   2024-01-15T10:30:05 proj_abc123 TOKENS_SENT input:1234 output:5678
   ```

3. **Review for Concerns**
   - Check that sensitive projects used privacy layer
   - Verify no unexpected API calls
   - Note any errors or failures

4. **Export if Needed**
   - Logs can be exported for compliance documentation
   - Filter by date range or project

---

## SOP-006: Adding a New Team Member

### Purpose
Grant access to Wowasi_ya for a new team member.

### When to Use
When onboarding new team members who need access.

### Roles Involved
- **Admin:** Creates account
- **New User:** Receives credentials

### Procedure

1. **Access User Management**
   - Web: Admin → Users → Add User
   - CLI: `wowasi_ya user add`

2. **Enter User Information**
   - Username
   - Email (optional)
   - Initial password (or generate random)

3. **Set Permissions**
   - Standard user: Can generate projects, view own history
   - Admin: Can manage users, view all logs, change config

4. **Create Account**
   - System creates account
   - Generates secure password if not provided

5. **Communicate Credentials**
   - Send username and password securely (not via email if possible)
   - Instruct user to change password on first login

6. **Verify Access**
   - New user logs in
   - Confirms can generate test project
