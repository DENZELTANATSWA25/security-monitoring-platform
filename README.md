# Security Monitoring Platform

### AI-Assisted Threat Detection & Security Operations

A full-stack security monitoring platform designed to collect security telemetry, detect suspicious activity, investigate incidents, and support security operations through a centralized web interface.

The application combines rule-based detection, anomaly-detection capabilities, real-time event streaming, incident management, analytics, and role-based administration.

Built using Python, FastAPI, Next.js, TypeScript, PostgreSQL, Redis, and Docker, the project demonstrates full-stack software engineering, API development, database design, authentication, automated testing, and security-focused application architecture.

> **Project status:** Full-stack V1 implemented and tested locally. Automated CI is operational. Additional security evaluation, performance testing, and production deployment are planned.

---

## Overview

Security teams need to collect and interpret events from multiple sources, identify suspicious behaviour, and investigate potential threats.

The Security Monitoring Platform provides a centralized application for managing these activities.

It supports:

- Security event collection and querying.
- External telemetry source registration and ingestion.
- Configurable rule-based threat detection.
- Anomaly-detection capabilities.
- Security alert management.
- Incident investigation and resolution workflows.
- Security analytics and reporting.
- Administrative audit logging.
- Role-based user management.
- Real-time security event streaming.

The platform is designed as a modular full-stack application, separating presentation, API endpoints, business logic, persistence, and supporting infrastructure.

---

## Key Features

### Security Event Monitoring

Collect, store, and investigate security events through a centralized interface.

Features include event querying, filtering, severity classification, and integration with the platform's detection and investigation workflows.

### Threat Detection

The backend supports deterministic detection rules and anomaly-based detection capabilities.

Detection rules can be configured and managed through dedicated API endpoints and the frontend interface.

### Security Alerts

Security alerts provide a structured mechanism for reviewing suspicious activity identified by the detection system.

The platform supports alert management and integration with incident investigation workflows.

### Incident Management

Investigate and manage security incidents through a structured lifecycle.

Implemented capabilities include:

- Incident creation and management.
- Incident assignment.
- Event and alert linking.
- Investigation notes.
- Evidence management.
- Incident activity tracking.
- Resolution workflows.

### Telemetry Source Management

Register and administer external telemetry sources.

Capabilities include:

- Telemetry source registration.
- Source authentication.
- Credential rotation.
- Ingestion validation.
- Ingestion rate limiting.
- Source health monitoring.

### Dashboard and Analytics

A centralized security operations dashboard provides visibility into monitored activity.

The platform includes operational metrics, security analytics, and reporting interfaces.

### User Administration and Access Control

The application implements three user roles:

| Role | Purpose |
|---|---|
| Administrator | Platform administration and user management |
| Analyst | Security investigation and operational workflows |
| Viewer | Read-only access to permitted information |

Authentication uses signed JSON Web Tokens (JWT).

Passwords are hashed using bcrypt.

The backend enforces role-based authorization, while the frontend provides role-aware navigation and interactions.

### Audit Logging

Administrative and security-relevant actions are recorded through the platform's audit logging functionality.

This supports accountability and investigation of user activity.

### Real-Time Event Streaming

The backend provides WebSocket-based security event streaming for real-time monitoring capabilities.

---

## Technology Stack

| Layer | Technologies |
|---|---|
| Frontend | Next.js, React, TypeScript, Tailwind CSS |
| UI Components | shadcn/ui |
| Frontend Data Management | TanStack Query, Zustand |
| Data Visualization | Recharts |
| Backend | Python 3.11, FastAPI |
| API | REST, WebSockets, OpenAPI |
| Database | PostgreSQL 15 |
| ORM | SQLAlchemy |
| Database Migrations | Alembic |
| Cache and Supporting Services | Redis 7 |
| Authentication | JWT, bcrypt |
| Containerization | Docker, Docker Compose |
| Backend Testing | pytest |
| Frontend Testing | Vitest |
| Continuous Integration | GitHub Actions |

---

## Architecture

The application follows a modular architecture with separate frontend, backend, and infrastructure components.

```text
                    ┌──────────────────────────┐
                    │       Web Browser        │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │     Next.js Frontend     │
                    │ React / TypeScript       │
                    └────────────┬─────────────┘
                                 │
                        REST / WebSocket
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │      FastAPI Backend     │
                    │                          │
                    │ API Routes               │
                    │ Authentication / RBAC    │
                    │ Business Services        │
                    │ Detection / Analytics    │
                    │ Incident Management      │
                    └───────────┬──────────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
                    ▼                       ▼
          ┌──────────────────┐    ┌──────────────────┐
          │   PostgreSQL     │    │      Redis       │
          │ Persistent Data  │    │ Supporting State │
          └──────────────────┘    └──────────────────┘
```

### Backend Organization

The FastAPI backend separates responsibilities across:

- **API endpoints:** HTTP and WebSocket interfaces.
- **Services:** Application business logic and security workflows.
- **Models:** SQLAlchemy database entities.
- **Schemas:** Request and response validation.
- **Core:** Configuration and security utilities.
- **Database:** Engine and session management.
- **Tests:** Automated backend verification.
- **Alembic:** Version-controlled database migrations.

This structure supports separation of concerns, maintainability, and independent testing.

---

## Repository Structure

```text
security-monitoring-platform/
├── .github/
│   └── workflows/
│       ├── backend-ci.yml
│       └── frontend-ci.yml
│
├── apps/
│   ├── backend/
│   │   ├── alembic/
│   │   ├── app/
│   │   ├── scripts/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── frontend/
│   │   ├── src/
│   │   ├── package.json
│   │   └── README.md
│   │
│   └── extension/
│       └── ...
│
├── docker-compose.yml
└── README.md
```

The browser extension directory contains early development work and is not part of the completed V1 application.

---

## Getting Started

The following instructions describe the local development environment.

### Prerequisites

Install:

- Git
- Docker with Docker Compose
- Node.js 22
- npm

The backend runs inside Docker, so a separate local Python installation is not required for the standard development setup.

### 1. Clone the Repository

Clone the project from GitHub:

```bash
git clone https://github.com/DENZELTANATSWA25/security-monitoring-platform.git
```

Navigate into the project directory:

```bash
cd security-monitoring-platform
```

### 2. Configure the Backend Environment

Copy the example environment file:

```bash
cp apps/backend/.env.example apps/backend/.env
```

Review the configuration in:

```text
apps/backend/.env
```

Ensure that:

- `DATABASE_URL` points to the PostgreSQL service.
- `REDIS_URL` points to Redis.
- `JWT_SECRET_KEY` contains a strong, unique secret.
- `CORS_ORIGINS` permits the frontend development address.

Generate a random JWT secret:

```bash
openssl rand -hex 32
```

Copy the generated value into `JWT_SECRET_KEY` in `apps/backend/.env`.

The Docker Compose configuration uses development database credentials.

**Do not reuse the example credentials or development configuration in production.**

Never commit `.env` files or authentication secrets.

### 3. Start the Backend Infrastructure

From the repository root:

```bash
docker compose up -d --build
```

This starts:

- PostgreSQL
- Redis
- FastAPI backend

Check the running services:

```bash
docker compose ps
```

### 4. Apply Database Migrations

Initialize the database schema:

```bash
docker compose exec backend alembic upgrade head
```

Alembic applies the version-controlled database migrations.

### 5. Create the Initial Administrator

Run the administrator bootstrap utility:

```bash
docker compose exec -it backend python -m scripts.bootstrap_admin
```

The utility prompts for administrator details and a password.

It creates an active, verified administrator account.

For security, the bootstrap utility refuses to create another administrator when one already exists.

**Do not include administrator credentials in scripts, command history, or committed files.**

### 6. Configure the Frontend

From the repository root, create the frontend environment file:

```bash
cp apps/frontend/.env.example apps/frontend/.env.local
```

Review `apps/frontend/.env.local` and ensure the API and WebSocket URLs match the endpoints configured by your backend.

For example:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws/events
NEXT_PUBLIC_DEV_AUTH_BYPASS=false
```

Keep development authentication bypass disabled.

### 7. Install Frontend Dependencies

Navigate into the frontend directory:

```bash
cd apps/frontend
```

Install the dependencies:

```bash
npm ci
```

### 8. Start the Frontend

Start the development server:

```bash
npm run dev
```

Keep this terminal running while using the application.

Open the frontend in your browser:

```text
http://localhost:3000
```

Sign in using the administrator account created during setup.

### 9. Verify the Installation

Once all services are running, check the following addresses:

| Service | Local Address |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API documentation | http://localhost:8000/docs |
| OpenAPI schema | http://localhost:8000/openapi.json |

Verify that:

1. The frontend loads successfully.
2. You can sign in with the administrator account.
3. The dashboard loads without API errors.
4. The backend API documentation is accessible.

### 10. Stop the Application

Stop the frontend development server by pressing `Ctrl + C` in its terminal.

From the repository root, stop the Docker services:

```bash
docker compose down
```

This stops the containers without deleting the PostgreSQL named volume.

**Warning:** Do not use `docker compose down -v` unless you intentionally want to delete the database volume and its stored data.

---

## API Documentation

The backend provides automatically generated OpenAPI documentation.

When the backend is running locally:

**Swagger UI**

```text
http://localhost:8000/docs
```

**OpenAPI Schema**

```text
http://localhost:8000/openapi.json
```

The API includes endpoints for authentication, user administration, security events, alerts, incidents, detection rules, telemetry, analytics, reporting, and audit logging.

---

## Testing

The project includes automated backend and frontend tests.

### Backend Tests

Backend tests use pytest.

Database tests require a dedicated PostgreSQL database named `security_test_db`.

This safeguard prevents tests from accidentally modifying the development database.

Create the test database if it does not already exist:

```bash
docker compose exec postgres psql -U admin -d postgres -c "CREATE DATABASE security_test_db;"
```

If the database already exists, this command will report an error; you do not need to recreate it.

Run the backend test suite using the dedicated test database:

```bash
docker compose exec \
  -e DATABASE_URL=postgresql+asyncpg://admin:admin@postgres:5432/security_test_db \
  backend python -m pytest tests/
```

The test database is separate from the application's development database.

### Frontend Tests

From the repository root:

```bash
npm --prefix apps/frontend run test
```

### Frontend Linting

```bash
npm --prefix apps/frontend run lint
```

### Frontend Production Build

```bash
npm --prefix apps/frontend run build
```

---

## Continuous Integration

GitHub Actions provides separate backend and frontend CI workflows.

### Backend CI

The backend workflow validates application changes through automated tests and coverage checks.

### Frontend CI

The frontend workflow runs:

1. Dependency installation.
2. Automated tests.
3. ESLint.
4. Production build.

Both workflows are configured to validate repository changes through GitHub Actions.

---

## Security Engineering

Security is a central consideration in the application's design.

Implemented controls include:

- Password hashing using bcrypt.
- JWT-based authentication.
- Role-based access control.
- Backend authorization checks.
- Login rate limiting.
- Telemetry source authentication.
- Telemetry ingestion validation.
- Ingestion rate limiting.
- Telemetry credential rotation.
- Audit logging.
- Environment-based secret configuration.
- Dedicated test database protection.
- Controlled initial administrator provisioning.

These controls reduce risk but do not constitute a guarantee that the application is free from vulnerabilities.

The current Docker Compose configuration is intended for local development and is **not production hardened**.

Further penetration testing, dependency review, deployment hardening, and security evaluation are planned.

---

## Project Status

### Completed

- Backend V1 implementation.
- Frontend V1 implementation.
- Full-stack browser integration testing.
- Authentication and role-based administration.
- Security event monitoring.
- Threat detection functionality.
- Alert and incident workflows.
- Telemetry ingestion and source administration.
- Dashboard, analytics, and reporting.
- Audit logging.
- Automated backend and frontend tests.
- GitHub Actions continuous integration.

### Planned

- Browser extension completion.
- Additional security testing and penetration testing.
- Load and performance evaluation.
- Production deployment and infrastructure hardening.
- Final system evaluation and demonstration.

---

## Engineering Focus

This project was developed to strengthen practical software engineering skills in:

- Full-stack application development.
- Modular backend architecture.
- REST API design.
- Relational database design and migrations.
- Authentication and authorization.
- Security-conscious software development.
- Automated testing and regression prevention.
- Containerized development environments.
- Continuous integration.
- Real-world application debugging and integration.

---

## License

No open-source license has been selected yet.

All rights remain reserved unless a license is added to the repository.