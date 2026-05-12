# FastOJ Constitution

<!--
  Sync Impact Report:
  - Version: 1.0.0 (NEW - initial constitution)
  - Added: 7 Core Principles, Technology Stack, Development Workflow, Governance
  - Templates requiring updates: All templates reference this as foundation
-->

## Core Principles

### I. Strict Frontend-Backend Separation
The system MUST maintain complete architectural separation between frontend and backend.
Frontend and backend are independent deployables with well-defined API contracts.
No shared state or direct database access from frontend.

**Rationale**: Ensures maintainability, scalability, and independent iteration of each layer.

### II. PostgreSQL-First Storage
PostgreSQL MUST be the primary data store for all persistent data.
All business entities, user data, and problem submissions MUST be stored in PostgreSQL.
No alternative primary databases permitted without explicit constitutional amendment.

**Rationale**: Ensures ACID compliance, relational data integrity, and enterprise-grade reliability.

### III. Redis + Message Queue for Async Processing
Redis MUST be used for caching and session management.
Message Queue (via Redis) MUST handle all asynchronous job processing, including but not limited to:
- Judge task dispatching
- Score recalculations
- Notification dispatches

**Rationale**: Decouples request handling from long-running operations, ensures system responsiveness.

### IV. Custom Sandbox (NON-NEGOTIABLE)
The judging sandbox MUST be built from scratch using Python Docker SDK.
Judge0 or any other pre-built judgment engine is strictly PROHIBITED.

The sandbox MUST implement:
- Network isolation: `network_mode='none'`
- Fork bomb protection: `pids_limit` set to reasonable limit
- CPU enforcement: cgroups-based CPU time limits for TLE detection
- Memory enforcement: cgroups-based memory limits for MLE detection
- Read-only filesystem: Mount code files as read-only during execution

**Rationale**: Security is paramount. Pre-built solutions introduce unknown attack vectors and cannot guarantee the isolation required for an OJ platform.

### V. Modular Route Architecture
All backend routes MUST be modular and decoupled.
Routes MUST be organized by domain (e.g., problems, submissions, users) in separate modules.
No monolithic route handlers permitted.

**Rationale**: Enables independent development, testing, and scaling of feature domains.

### VI. Judge Worker Decoupling
Judge Worker MUST be completely decoupled from Web API.
Communication MUST occur via message queue (Redis).
Web API enqueues judge tasks; Worker picks up tasks, executes, and updates results.
Both components MUST be independently deployable via docker-compose with physical isolation.

**Rationale**: Ensures judge execution does not impact API responsiveness; enables horizontal scaling of workers.

### VII. Docker-Compose Deployment Ready
The entire system MUST be deployable via docker-compose on a single Linux VPS.
All services (API, Worker, PostgreSQL, Redis) MUST be containerized with proper isolation.
Physical isolation between API and Worker containers MUST be maintained.

**Rationale**: Simplifies deployment, ensures consistent environments, and maintains security boundaries.

## Technology Stack

### Backend Requirements
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Database**: PostgreSQL (required)
- **Cache/Queue**: Redis (required) + Message Queue
- **Container**: Python Docker SDK for sandbox

### Sandbox Security Requirements
- Network: Completely disabled (`network_mode='none'`)
- Process limits: Restricted via `pids_limit`
- CPU limits: cgroups-based enforcement for TLE
- Memory limits: cgroups-based enforcement for MLE
- Filesystem: Read-only mount for submitted code

### Project Structure
```
backend/
├── api/           # FastAPI routes (modular by domain)
├── worker/        # Judge worker (decoupled)
├── sandbox/       # Docker-based execution sandbox
├── models/        # SQLAlchemy/Pydantic models
└── services/      # Business logic services
```

## Development Workflow

### Code Organization
1. All API routes MUST reside in domain-specific modules under `backend/api/`
2. Judge worker MUST be a separate process/service, communicating only via message queue
3. Sandbox logic MUST be isolated in its own module with no direct API exposure

### Testing Requirements
- Unit tests for all services and models
- Integration tests for API endpoints
- Sandbox security tests (verify isolation)
- Worker-API contract tests

### Deployment Pipeline
1. All services containerized
2. docker-compose orchestrates all components
3. Environment-based configuration (no hardcoded values)

## Governance

### Constitution Supremacy
This constitution supersedes all other development practices.
Any deviation from these principles requires a formal constitutional amendment.

### Amendment Procedure
1. Proposal: Document the principle change with rationale
2. Review: Cross-team review of security/compatibility implications
3. Approval: Majority approval required
4. Migration: Document migration plan for existing implementations

### Compliance Verification
All PRs MUST verify compliance with constitutional principles:
- Technology stack choices align with required choices
- Sandbox implementations use custom Docker SDK (no Judge0)
- Worker decoupling maintained
- Security measures implemented per sandbox requirements

### Versioning
- **Version**: 1.0.0
- **Ratified**: 2026-03-16
- **Last Amended**: 2026-03-16
