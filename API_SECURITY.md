# API Security Documentation

This document describes all API endpoints in Wowasi Ya, their authentication requirements, and security rationale.

---

## Authentication Method

Wowasi Ya uses **HTTP Basic Authentication** for protected endpoints. Authentication is handled via the `RequireAuth` dependency.

- **Username/Password**: Configured via `ADMIN_USERNAME` and `ADMIN_PASSWORD` environment variables
- **Token Lifetime**: 24 hours (for JWT-based flows)
- **Algorithm**: HS256

---

## Endpoint Security Summary

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/api/v1/health` | GET | No | Health check with LLM status |
| `/api/v1/projects` | POST | **Yes** | Create a new project |
| `/api/v1/projects` | GET | No | List all projects |
| `/api/v1/projects/{id}/discovery` | GET | **Yes** | Get discovery and privacy results |
| `/api/v1/projects/{id}/approve` | POST | **Yes** | Approve privacy and start generation |
| `/api/v1/projects/{id}/status` | GET | **Yes** | Check generation progress |
| `/api/v1/projects/{id}/result` | GET | **Yes** | Download generated documents |
| `/api/v1/projects/{id}/publish-to-outline` | POST | **Yes** | Publish to Outline Wiki |
| `/api/v1/projects/{id}/next-steps` | POST | **Yes** | Create next steps for project |
| `/api/v1/projects/{id}/next-steps` | GET | No | List next steps for project |
| `/api/v1/projects/{id}/next-steps/{step_id}` | GET | **Yes** | Get specific next step |
| `/api/v1/projects/{id}/next-steps/{step_id}` | PATCH | **Yes** | Update next step |
| `/api/v1/projects/{id}/next-steps/{step_id}/complete` | POST | **Yes** | Mark step complete |
| `/api/v1/projects/{id}/next-steps/{step_id}/skip` | POST | **Yes** | Skip a step |
| `/api/v1/projects/{id}/progress` | GET | No | Get project progress metrics |

---

## Detailed Endpoint Reference

### Health Check

```
GET /api/v1/health
```

**Authentication**: Not required

**Purpose**: System health monitoring and LLM provider status check.

**Security Rationale**: Health endpoints are intentionally public to support:
- Load balancer health probes
- Monitoring systems (Uptime Kuma, Prometheus)
- Quick diagnostics without credentials

**Response**: Returns system status, configured providers, and Llama CPP availability.

---

### Create Project

```
POST /api/v1/projects
```

**Authentication**: Required

**Purpose**: Create a new project and initiate Phase 0 (Agent Discovery).

**Security Rationale**: Protected because:
- Initiates local processing (CPU/memory usage)
- Creates state that persists in memory
- First step in a workflow that may lead to API costs

**Request Body**:
```json
{
  "name": "Project Name",
  "description": "Detailed project description",
  "additional_context": "Optional extra context",
  "output_format": "filesystem",
  "area": "04_Iyeska"
}
```

---

### List Projects

```
GET /api/v1/projects
```

**Authentication**: Not required

**Purpose**: List all projects with basic metadata.

**Security Rationale**: Public read access supports:
- Portal dashboard viewing
- Quick project lookup
- Read-only operations don't need protection

**Note**: Only returns basic info (id, name, status, created_at). Detailed data requires authentication.

---

### Get Discovery Results

```
GET /api/v1/projects/{project_id}/discovery
```

**Authentication**: Required

**Purpose**: Retrieve agent discovery and privacy scan results.

**Security Rationale**: Protected because:
- Contains detailed project analysis
- Includes privacy flags (PII/PHI detection results)
- Provides full agent definitions

---

### Approve Privacy

```
POST /api/v1/projects/{project_id}/approve
```

**Authentication**: Required

**Purpose**: Human approval gate before API calls. Starts background generation.

**Security Rationale**: Protected because:
- Triggers expensive API calls (Claude research, document generation)
- Represents explicit user consent for data processing
- Can incur costs of $2-5 per project

**Request Body**:
```json
{
  "approved": true,
  "use_sanitized": true
}
```

---

### Get Project Status

```
GET /api/v1/projects/{project_id}/status
```

**Authentication**: Required

**Purpose**: Check generation progress (phase, document count, errors).

**Security Rationale**: Protected because:
- Reveals internal processing state
- May contain error messages with sensitive details

---

### Get Project Result

```
GET /api/v1/projects/{project_id}/result
```

**Authentication**: Required

**Purpose**: Download all generated documents.

**Security Rationale**: Protected because:
- Contains full document content
- May include business-sensitive information
- Represents significant generated value

---

### Publish to Outline

```
POST /api/v1/projects/{project_id}/publish-to-outline
```

**Authentication**: Required

**Purpose**: Push generated documents to Outline Wiki.

**Security Rationale**: Protected because:
- Creates external resources (Outline collections)
- Can enable public sharing links
- Modifies data in connected systems

**Request Body**:
```json
{
  "enable_sharing": false
}
```

---

### Create Next Steps

```
POST /api/v1/projects/{project_id}/next-steps
```

**Authentication**: Required

**Purpose**: Create actionable next steps for a project.

**Security Rationale**: Protected because:
- Creates persistent state
- Initializes workflow tracking

**Request Body**:
```json
{
  "document_types": ["project_brief", "risks"]
}
```

---

### List Next Steps

```
GET /api/v1/projects/{project_id}/next-steps
```

**Authentication**: Not required

**Query Parameters**: `document_type` (optional filter)

**Purpose**: Retrieve all next steps for a project.

**Security Rationale**: Public read access supports:
- Portal progress tracking
- Read-only dashboard views
- Progress visibility for stakeholders

---

### Get Specific Next Step

```
GET /api/v1/projects/{project_id}/next-steps/{step_id}
```

**Authentication**: Required

**Purpose**: Get detailed information about a specific step.

**Security Rationale**: Protected because:
- Contains action configuration details
- May include internal workflow data

---

### Update Next Step

```
PATCH /api/v1/projects/{project_id}/next-steps/{step_id}
```

**Authentication**: Required

**Purpose**: Update step status, notes, or output data.

**Security Rationale**: Protected because:
- Modifies persistent state
- Tracks user actions and assignments

**Request Body**:
```json
{
  "status": "in_progress",
  "notes": "Working on this",
  "output_data": {}
}
```

---

### Complete Next Step

```
POST /api/v1/projects/{project_id}/next-steps/{step_id}/complete
```

**Authentication**: Required

**Purpose**: Mark a step as completed.

**Security Rationale**: Protected to ensure:
- Only authorized users can mark completion
- Completion is tracked with attribution

**Request Body**:
```json
{
  "completed_by": "user@example.com",
  "output_data": {}
}
```

---

### Skip Next Step

```
POST /api/v1/projects/{project_id}/next-steps/{step_id}/skip
```

**Authentication**: Required

**Purpose**: Mark a step as skipped.

**Security Rationale**: Protected because:
- Modifies workflow state
- Requires reason documentation

**Request Body**:
```json
{
  "reason": "Not applicable to this project"
}
```

---

### Get Project Progress

```
GET /api/v1/projects/{project_id}/progress
```

**Authentication**: Not required

**Purpose**: Get aggregate progress metrics.

**Security Rationale**: Public read access supports:
- Dashboard progress bars
- Stakeholder visibility
- High-level tracking without sensitive details

---

## Security Recommendations

### For Production Deployment

1. **Use HTTPS**: Always deploy behind Cloudflare or Traefik with TLS termination
2. **Strong Passwords**: Generate secure `ADMIN_PASSWORD` values
3. **Rotate Credentials**: Change passwords periodically
4. **Rate Limiting**: Configure Cloudflare or nginx rate limits on auth endpoints
5. **IP Allowlisting**: Consider restricting API access to known IP ranges

### Environment Variables

```bash
# Required for authentication
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<strong-password>
SECRET_KEY=<random-256-bit-key>

# Generate a secure secret key:
# python -c "import secrets; print(secrets.token_hex(32))"
```

### Future Enhancements

- OAuth2/OIDC integration with Zitadel
- Role-based access control (viewer, editor, admin)
- API key authentication for service accounts
- Audit logging of authentication events

---

## API Documentation

Interactive API documentation is available at:

- **Local**: http://localhost:8001/docs
- **Production**: https://wowasi.iyeska.net/docs

The OpenAPI spec includes authentication requirements and request/response schemas.
