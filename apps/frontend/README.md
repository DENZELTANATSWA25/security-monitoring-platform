# Security Monitoring Platform — Frontend

The frontend application for the Security Monitoring Platform, built with Next.js, React, and TypeScript.

It provides a web-based security operations interface for monitoring events, reviewing alerts, investigating incidents, managing detection rules, and administering the platform.

The frontend communicates with the FastAPI backend through REST APIs and WebSockets.

> **Status:** Frontend V1 implemented and tested locally. Production deployment and additional security and performance evaluation remain planned.

---

## Technology Stack

| Technology | Purpose |
|---|---|
| Next.js 16 | React application framework |
| React 19 | User interface development |
| TypeScript | Static typing |
| Tailwind CSS 4 | Styling |
| shadcn/ui | Reusable UI components |
| TanStack Query | Server-state management |
| Zustand | Client-side state management |
| Axios | HTTP API communication |
| Recharts | Data visualization |
| Vitest | Automated testing |
| ESLint | Static code analysis |

---

## Features

The frontend provides interfaces for:

- **Dashboard:** Overview of security activity and operational metrics.
- **Security Events:** Browse and investigate collected telemetry.
- **Alerts:** Review and manage detected threats.
- **Incidents:** Manage security investigations and incident workflows.
- **Detection Rules:** View and manage detection configurations.
- **Analytics:** Explore security metrics and trends.
- **Reports:** Access security reporting functionality.
- **User Administration:** Manage users and access permissions.
- **Settings:** Access supported platform configuration options.

### Authentication and Authorization

The frontend integrates with the backend's JWT authentication system.

It includes authenticated API requests, session handling, role-aware navigation, and permission-based interface behaviour.

The backend remains responsible for enforcing authorization.

### Real-Time Updates

The frontend establishes an authenticated WebSocket connection to receive security event notifications.

Relevant dashboard and event queries are refreshed when new security events arrive.

---

## Getting Started

The frontend requires a running Security Monitoring Platform backend.

For complete instructions covering Docker, PostgreSQL, Redis, database migrations, and initial administrator creation, see the [root project README](../../README.md).

### Prerequisites

- Node.js 22
- npm
- Running FastAPI backend

### 1. Install Dependencies

From the repository root:

```bash
cd apps/frontend
npm ci
```

### 2. Configure Environment Variables

Create the local environment file:

```bash
cp .env.example .env.local
```

Configure the following values:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws/events
NEXT_PUBLIC_DEV_AUTH_BYPASS=false
```

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_API_URL` | FastAPI REST API base URL |
| `NEXT_PUBLIC_WS_URL` | WebSocket endpoint for security events |
| `NEXT_PUBLIC_DEV_AUTH_BYPASS` | Development authentication bypass setting; keep disabled |

Environment variables prefixed with `NEXT_PUBLIC_` are exposed to browser-side code.

Do not place passwords, API secrets, or private credentials in these variables.

### 3. Start the Development Server

```bash
npm run dev
```

Open:

```text
http://localhost:3000
```

Sign in using an account provisioned through the backend.

---

## Development Commands

Run these commands from `apps/frontend`:

| Command | Purpose |
|---|---|
| `npm run dev` | Start the development server |
| `npm run build` | Create a production build |
| `npm run start` | Start the built application |
| `npm run lint` | Run ESLint |
| `npm run test` | Execute automated tests |
| `npm run test:watch` | Run tests in watch mode |
| `npm run test:coverage` | Generate test coverage results |

---

## API Integration

The frontend uses a centralized Axios client configured in:

```text
src/services/api.ts
```

The client:

- Uses `NEXT_PUBLIC_API_URL` as its base URL.
- Attaches the current JWT to authenticated requests.
- Handles authentication failures.

### WebSocket Integration

Real-time event handling is implemented in:

```text
src/hooks/use-live-events.ts
```

The hook establishes a WebSocket connection using `NEXT_PUBLIC_WS_URL`.

When a security event notification is received, relevant TanStack Query caches are invalidated to refresh displayed information.

---

## Testing and Quality

The frontend uses Vitest for automated testing and ESLint for static analysis.

Run the test suite:

```bash
npm run test
```

Check code quality:

```bash
npm run lint
```

Verify that the application builds:

```bash
npm run build
```

Frontend CI runs automated tests, linting, and a production build through GitHub Actions.

The workflow is defined in:

```text
.github/workflows/frontend-ci.yml
```

This path is relative to the repository root.

---

## Security Considerations

The frontend implements authentication-aware navigation and interfaces, but server-side authorization is enforced by the FastAPI backend.

Security-related considerations include:

- JWT-based authenticated API requests.
- Role-aware interface behaviour.
- Handling expired or rejected authentication tokens.
- Environment-based API configuration.
- Avoiding private credentials in public frontend environment variables.

The current implementation is intended for local development and evaluation.

Additional security hardening and production deployment work remain planned.

---

## Project Documentation

For backend architecture, database setup, security controls, full-stack features, and overall project status, refer to the [main project README](../../README.md).