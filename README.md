# Semantic Bridge Server

Event-driven API server built with FastAPI.

## Structure

```
src/
├── api/                    # API layer
│   ├── routes/            # API endpoints
│   ├── middleware/        # Custom middleware
│   └── dependencies/      # Dependency injection
├── modules/               # Core modules
│   └── core/
│       ├── event_bus/     # Event bus implementation
│       └── telemetry/     # Logging and monitoring
└── services/              # Business logic services
```

## Setup

1. Copy `.env.example` to `.env` and configure your database:
```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/semantic_bridge
```

2. Install dependencies:
```bash
poetry install
```

3. Run migrations:
```bash
poetry run alembic upgrade head
```

## Run

```bash
poetry run python main.py
```

Server runs on http://localhost:8000

## Endpoints

- `GET /health` - Health check endpoint
- `GET /docs` - API documentation

## Database Migrations

Create a new migration:
```bash
poetry run alembic revision --autogenerate -m "description"
```

Apply migrations:
```bash
poetry run alembic upgrade head
```
