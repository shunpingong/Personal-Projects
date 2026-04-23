# trust_system

Async FastAPI backend for Trust & Safety operations with JWT authentication, RBAC, moderation workflows, PostgreSQL, Alembic, and Docker.

## Stack

- FastAPI with async route handlers
- SQLAlchemy 2.x async ORM
- PostgreSQL
- JWT access and refresh tokens
- Pydantic v2 schemas
- Alembic migrations
- Docker and Docker Compose

## Project Structure

```text
Trust_System/
  docker-compose.yml
  README.md
  backend/
    .dockerignore
    .env
    .env.example
    Dockerfile
    requirements.txt
    alembic.ini
    alembic/
      env.py
      script.py.mako
      versions/
        20260423_01_initial_schema.py
    app/
      main.py
      api/
        routes.py
      core/
        config.py
        enums.py
        security.py
      db/
        base.py
        session.py
        models/
          report.py
          user.py
      modules/
        auth/
          dependencies.py
          routes.py
        moderation/
          routes.py
        users/
          routes.py
      schemas/
        auth.py
        common.py
        report.py
        user.py
      services/
        auth_service.py
        bootstrap_service.py
        moderation_service.py
        user_service.py
    infrastructure/
      aws/
        base.py
        s3.py
        sqs.py
      kafka/
        base.py
        service.py
```

## Features

### Authentication

- `POST /api/v1/auth/register` registers a user with the default `user` role
- `POST /api/v1/auth/login` returns access and refresh tokens
- `POST /api/v1/auth/refresh` rotates a token pair from a valid refresh token
- `GET /api/v1/auth/me` returns the authenticated user

### Users

- `GET /api/v1/users` lists users for `admin` and `moderator`
- `GET /api/v1/users/{user_id}` returns a user for privileged roles or the same user
- `POST /api/v1/users` creates a user for `admin`
- `PATCH /api/v1/users/{user_id}` updates a user
- `DELETE /api/v1/users/{user_id}` deletes a user for `admin`

### Moderation

- `POST /api/v1/moderation/reports` creates a moderation report
- `GET /api/v1/moderation/reports` lists reports for `admin` and `moderator`
- `GET /api/v1/moderation/reports/{report_id}` gets a report
- `PATCH /api/v1/moderation/reports/{report_id}/status` updates report status to `pending`, `reviewed`, or `escalated`

### Infrastructure Stubs

- `infrastructure/kafka/` contains producer and consumer interfaces with no-op service skeletons
- `infrastructure/aws/` contains S3 and SQS abstractions with in-memory or logging-backed stubs

## Configuration

Environment values live in `backend/.env`. The defaults are development-safe and intended for local Docker usage.

Important variables:

- `SECRET_KEY`: signing key for JWTs
- `ACCESS_TOKEN_EXPIRE_MINUTES`: access token lifetime
- `REFRESH_TOKEN_EXPIRE_DAYS`: refresh token lifetime
- `POSTGRES_*`: PostgreSQL connection settings
- `CORS_ORIGINS`: JSON array of allowed origins
- `BOOTSTRAP_ADMIN_*`: one-time bootstrap admin credentials used on startup if that email does not already exist

When running the API inside Docker Compose, `POSTGRES_SERVER` is overridden to `postgres`.

The default development bootstrap admin is:

- email: `admin@trustsystem.local`
- password: `AdminPassword123!`

## Running with Docker

From `Trust_System/`:

```bash
docker compose up --build
```

The API will be available at:

- `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/v1/health`

## Running Locally

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r backend/requirements.txt
```

3. Start PostgreSQL locally or run only the database via Docker:

```bash
docker compose up -d postgres
```

4. Apply migrations from `backend/`:

```bash
alembic upgrade head
```

5. Start the API from `backend/`:

```bash
uvicorn app.main:app --reload
```

## Alembic

Create new migrations from `backend/` with:

```bash
alembic revision --autogenerate -m "describe change"
```

Apply them with:

```bash
alembic upgrade head
```

## Example Requests

Register:

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","full_name":"Trust Analyst","password":"supersecurepassword"}'
```

Login:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"supersecurepassword"}'
```

Create a report:

```bash
curl -X POST http://localhost:8000/api/v1/moderation/reports \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"subject":"Abusive message","category":"harassment","description":"User sent repeated threats."}'
```

## Notes

- Passwords are hashed with bcrypt via Passlib.
- Protected routes use JWT bearer authentication and role checks.
- A bootstrap admin is created on startup when `BOOTSTRAP_ADMIN_EMAIL` and `BOOTSTRAP_ADMIN_PASSWORD` are set and that user does not already exist.
- Refresh tokens are stateless in this implementation. If token revocation is required later, add a persisted token registry or denylist.
- AWS and Kafka integrations are intentionally brokerless/clientless stubs so the project is runnable without external credentials.
