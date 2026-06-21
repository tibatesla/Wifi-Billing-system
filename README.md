# Wi-Fi Billing SaaS

## Project Summary

This repository contains a Wi-Fi billing system built with:

- **Backend**: FastAPI + SQLAlchemy + async PostgreSQL + Celery
- **Payment integration**: Safaricom M-Pesa via Daraja
- **Router provisioning**: MikroTik RouterOS API
- **Frontend**: React + Vite (starter UI)

The system is designed to support ISP hotspot management, tenant-scoped billing, and automatic subscription expiration.

> Note: Some backend files and frontend UI components are placeholders or incomplete. The app currently includes working backend logic for auth, M-Pesa payment initiation, and router integration, while the frontend remains a starter shell.

---

## Repository Layout

```
/wi-fi
  README.md                 # This file
  requirements.txt          # Python backend dependencies
  backend/
    app/
      main.py               # FastAPI app entrypoint
      worker.py             # Celery expiration worker
      api/
      core/
      db/
      services/
    migrations/
    Dockerfile             # empty placeholder
    docker-compose.yml     # empty placeholder
    requirements.txt       # currently empty
  frontend/
    package.json           # React / Vite dependencies
    src/                   # React starter UI
```

There is also a duplicate top-level `app/` package in the repository root that mirrors some backend logic, but the active backend app is under `backend/app/`.

---

## Backend Architecture

### Main entrypoint

- `backend/app/main.py`
  - Creates the FastAPI application
  - Configures CORS for local frontend development
  - Registers routes:
    - `/api/v1/auth`
    - `/api/v1/mpesa`
    - `/api/v1/admin`
  - Exposes `/health`

### Configuration

- `backend/app/core/config.py`
  - Defines application settings using Pydantic settings
  - Includes database URL, JWT settings, and a hard-coded `LOCAL_TENANT_ID`

- `backend/app/core/security.py`
  - Provides password hashing and verification
  - Creates JWT access tokens
  - Uses `HS256`

### Database

- `backend/app/db/session.py`
  - Configures SQLAlchemy async engine and session factory
  - Provides `get_db()` dependency for FastAPI

- `backend/app/db/models.py`
  - Defines core database models:
    - `Tenant`
    - `User`
    - `Router`
    - `Plan`
    - `Customer`
    - `Subscription`
    - `Transaction`
  - Relationships are tenant-scoped and include referential integrity

---

## API Endpoints

### Authentication

- `backend/app/api/v1/endpoints/auth.py`
  - `POST /api/v1/auth/login`
  - Uses `OAuth2PasswordRequestForm`
  - Returns JWT token with tenant and role claims

### M-Pesa Payment Flow

- `backend/app/api/v1/endpoints/mpesa.py`
  - `POST /api/v1/mpesa/stk-push`
    - Fetches tenant-specific Daraja credentials and plan pricing
    - Initiates M-Pesa STK Push
    - Creates a pending `Transaction`
  - `POST /api/v1/mpesa/callback/{tenant_id}`
    - Receives Safaricom callback
    - Processes success and failure results
    - Enqueues a background task to activate the customer on MikroTik

### Router Management

- `backend/app/api/v1/endpoints/routers.py`
  - `GET /api/v1/routers/`
  - `DELETE /api/v1/routers/{router_id}`
  - Uses tenant scoping and role-based access control

### Customer Creation

- `backend/app/api/v1/endpoints/customers.py`
  - `POST /api/v1/customers/`
  - Creates a local customer record for the locked tenant

### Notes

- `backend/app/api/v1/endpoints/tenants.py` is currently empty
- `backend/app/api/v1/endpoints/customers.py` is incomplete and may need fixes

---

## Service Layer

### M-Pesa / Daraja

- `backend/app/services/mpesa_service.py`
  - `DarajaService` handles Daraja OAuth token retrieval and STK Push requests
  - Uses `httpx.AsyncClient`
  - Supports sandbox and production URL patterns

### MikroTik integration

- `backend/app/services/mikrotik_service.py`
  - Connects to MikroTik RouterOS using `routeros_api`
  - Activates, suspends, and checks hotspot users
  - Contains both synchronous router operations and async wrappers

### Billing

- `backend/app/services/billing_service.py`
  - Creates or extends subscriptions
  - Extends active subscription expiry when a user pays again

### SMS

- `backend/app/services/sms_service.py`
  - Sends SMS through Africa's Talking
  - Formats Kenyan phone numbers

---

## Background Worker

- `backend/app/worker.py`
  - Defines a Celery app with Redis broker/backend
  - Runs a scheduled task every minute to expire subscriptions
  - Marks eligible `Subscription` records as `EXPIRED`

> There is also a duplicate `app/worker.py` at the repo root, which appears to be a parallel or legacy copy of the same worker logic.

---

## Frontend

The frontend is a Vite + React app scaffolding for the Wi-Fi Billing system.

Key files:

- `frontend/package.json`
  - React 19 + Vite 8
  - TypeScript support
- `frontend/src/main.tsx`
  - React app bootstrap
- `frontend/src/App.tsx`
  - Router configuration and public/admin route setup
- `frontend/src/CaptivePortal.tsx`
  - Customer captive portal and M-Pesa checkout flow
- `frontend/src/AdminLogin.tsx`
  - Admin login screen with session-based protection
- `frontend/src/AdminDashboard.tsx`
  - Admin dashboard with tenant dashboard stats and router management UI
- `frontend/src/App.css`
  - Basic styling

### Current status

- The frontend now includes:
  - customer captive portal page
  - admin login page
  - protected admin dashboard route
  - M-Pesa payment checkout flow in `CaptivePortal`
  - admin dashboard tabbed interface for dashboard, routers, and settings
- The frontend still needs backend API wiring for full production use.

---

## Setup Instructions

### Backend

1. Create a Python environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Configure database settings in `backend/app/core/config.py`:

- `DATABASE_URL`
- `SECRET_KEY`
- `LOCAL_TENANT_ID` if you want single-tenant behavior

3. Run database migrations:

```bash
cd backend
alembic upgrade head
```

4. Run the API server:

```bash
uvicorn backend.app.main:app --reload
```

5. Run the Celery worker:

```bash
cd backend
celery -A backend.app.worker worker --beat --loglevel=info
```

> The worker uses Redis at `redis://localhost:6379/0`.

### Frontend

1. Install dependencies:

```bash
cd frontend
npm install
```

2. Run the development server:

```bash
npm run dev
```

3. Open the Vite URL shown in the terminal.

---

## Important Caveats

- `backend/Dockerfile` and `backend/docker-compose.yml` are empty placeholders.
- The repository contains a duplicated `app/` package at the root; the true backend is under `backend/app/`.
- The backend currently enforces a hard-coded tenant ID through `LOCAL_TENANT_ID` and `app/api/dependencies/tenant.py`.
- The frontend is not implemented beyond the starter Vite sample.
- `backend/app/api/v1/endpoints/tenants.py` is empty and should be implemented for tenant management.

---

## Recommended Next Steps

1. Wire the frontend to backend API endpoints.
2. Implement tenant and customer management endpoints.
3. Add validation and Pydantic schemas for request/response models.
4. Complete router onboarding and payment reconciliation flows.
5. Add proper environment loading and secret management for Daraja credentials.
6. Fill in Docker deployment files.

---

## File Summary

### Backend
- `backend/app/main.py`
- `backend/app/core/config.py`
- `backend/app/core/security.py`
- `backend/app/db/session.py`
- `backend/app/db/models.py`
- `backend/app/api/v1/endpoints/auth.py`
- `backend/app/api/v1/endpoints/mpesa.py`
- `backend/app/api/v1/endpoints/routers.py`
- `backend/app/api/v1/endpoints/customers.py`
- `backend/app/services/mpesa_service.py`
- `backend/app/services/mikrotik_service.py`
- `backend/app/services/billing_service.py`
- `backend/app/services/sms_service.py`
- `backend/app/worker.py`

### Frontend
- `frontend/package.json`
- `frontend/src/main.tsx`
- `frontend/src/App.tsx`
- `frontend/src/App.css`

---

## Contact

If you want, I can also help create:
- an improved backend `README` with API docs,
- a frontend architecture plan,
- or a `docker-compose.yml` and `Dockerfile` for deployment.
