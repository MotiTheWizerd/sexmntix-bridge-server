Hi, my name is Moti. Welcome back to the **Semantix Bridge Server** project!

## Main Tech Libraries
- **git** - source control
- **Poetry**  - handle packages
- **fastapi** - Modern async web framework for building APIs
- **uvicorn** - ASGI server for FastAPI
- **sqlalchemy** - SQL toolkit and ORM for database operations
- **asyncpg** - Fast PostgreSQL database client for async operations
- **alembic** - Database migration tool for SQLAlchemy
- **pydantic** - Data validation using Python type hints
- **python-socketio** - Real-time bidirectional communication
- **chromadb** - Vector database for semantic search and embeddings
- **httpx** - Modern HTTP client for async requests
- **mcp** - Model Context Protocol for AI tool integration
- **python-dotenv** - Environment variable management
- **bcrypt** + **passlib** - Password hashing and security

## What We're Building

**Semantix Bridge Server** is the Python-based backend that powers the Semantix VS Code extension (built in a separate project). This server is responsible for:
- **API Endpoints**: REST API for the VS Code extension to communicate with
- **Semantix Bridge Logic**: Core business logic for semantic memory, vector search, and AI capabilities
- **Data Persistence**: Managing PostgreSQL database and ChromaDB vector storage
- **MCP Integration**: Providing MCP tools for Claude Desktop and other AI clients

### Tech Stack
- **Language**: Python 3.11+
- **Package Manager**: Poetry
- **Web Framework**: FastAPI with Uvicorn
- **Database**: PostgreSQL (via SQLAlchemy + Alembic migrations)
- **Vector Storage**: ChromaDB (local persistent storage)
- **Embeddings**: Google's text-embedding-004 model
- **Protocols**: MCP (Model Context Protocol) for AI tool integration
- **Real-time**: Socket.IO for live metrics streaming
- **Event Architecture**: Custom EventBus for decoupled event-driven design

## Core Features Implemented

### 1. Semantic Memory System
- **Memory Logs**: Long-term searchable knowledge with vector embeddings
- **Mental Notes**: Short-term session-based contextual notes
- **Vector Search**: Semantic similarity search via ChromaDB
- **Multi-tenant Isolation**: Per-user/per-project data separation

### 2. MCP Server (XCP Module)
- **Tools Available**:
  - `semantic_search` - Search memories by semantic similarity
  - `store_memory` - Save long-term knowledge
  - `query_mental_notes` - Retrieve session notes
  - `store_mental_note` - Record contextual thoughts
  - `generate_embedding` - Create text embeddings
- **Transport**: Stdio-based MCP protocol
- **Integration**: Works with Claude Desktop and other MCP clients
- **Run command**: `python -m src.modules.xcp_server`

### 3. FastAPI REST API
- `/health` - Health check endpoint
- `/api/memory-logs/*` - Memory log CRUD operations
- `/api/mental-notes/*` - Mental notes management
- `/api/embeddings/*` - Embeddings generation
- `/api/users/*` - User management
- `/api/monitoring/*` - System metrics
- Real-time Socket.IO for live metrics streaming

### 4. Event-Driven Architecture
- **EventBus**: Centralized pub/sub system for loose coupling
- **Event Emitters**: Automatic event publishing for memory, user, and system events
- **Metrics Collection**: ChromaDB performance monitoring (search speed, storage health, ingestion metrics)
- **Real-time Streaming**: Metrics pushed to connected clients via Socket.IO

### 5. Modular Architecture (Recent Refactoring Work)
- **XCP Server Tools**: Modular packages with separation of concerns
  - `config.py` - Tool definitions and constants
  - `validators.py` - Argument validation
  - `formatters.py` - Response formatting
  - `tool.py` - Main orchestration
- **ChromaDB Infrastructure**: Collection management, operations, caching
- **Dependency Injection**: Service container with auto-discovery patterns
- **Composition Pattern**: Moved from inheritance to composition for flexibility

## Project Structure

```
src/
├── api/                          # FastAPI application layer
│   ├── routes/                   # REST API endpoints
│   ├── middleware/               # Custom middleware (logging, CORS)
│   ├── dependencies/             # DI for API routes
│   └── app.py                    # FastAPI app initialization
├── database/                     # PostgreSQL persistence
│   ├── models/                   # SQLAlchemy models
│   ├── repositories/             # Data access layer
│   └── connection.py             # Database session management
├── events/                       # Event system
│   ├── emitters/                 # Event emitters (memory, user, etc.)
│   └── schemas.py                # Event type definitions
├── infrastructure/               # External integrations
│   └── chromadb/                 # ChromaDB client and operations
│       ├── client.py             # ChromaDB client wrapper
│       ├── collection/           # Collection management
│       └── operations/           # CRUD operations
├── modules/                      # Core business modules
│   ├── core/
│   │   ├── event_bus/            # EventBus implementation
│   │   ├── telemetry/            # Logging and monitoring
│   │   └── di/                   # Dependency injection container
│   ├── embeddings/               # Embedding service
│   │   ├── providers/google/     # Google embedding provider
│   │   ├── caching/              # Embedding cache
│   │   └── service/              # Embedding service
│   ├── vector_storage/           # Vector storage module
│   │   ├── search/               # Semantic search handlers
│   │   └── storage/              # Storage operations
│   └── xcp_server/               # MCP server module
│       ├── protocol/             # MCP protocol implementation
│       ├── tools/                # MCP tools (search, memory, notes)
│       └── service/              # XCP service orchestration
└── services/                     # Application services
    ├── chromadb_metrics/         # Metrics collection service
    └── socket_service.py         # Socket.IO service
```

## Claude's Memory System

I use the MCP tools to maintain context across our work sessions:

### 🧠 Mental Notes (Short-term session memory)
- `store_mental_note(content, note_type)` - Record thoughts during current session
  - Types: `"note"`, `"decision"`, `"observation"`, `"context"`, `"insight"`
  - Session-scoped, chronological narrative
  - Used to maintain context across conversations
- `query_mental_notes()` - Read current session's notes
- `query_mental_notes(session_id: "mcp_session_...")` - Read specific past session
- `query_mental_notes(limit: 50)` - Get recent notes across all sessions

### 📚 Memory Logs (Long-term searchable knowledge)
- `store_memory(content, task, agent, tags, metadata)` - Store permanent structured knowledge
  - Automatically embedded for semantic search
  - Use for: solutions, patterns, gotchas, learnings, architecture decisions
  - Tags help categorize (max 5 tags)
- `semantic_search(query, limit, min_similarity)` - Search all memories semantically
  - Returns relevant memories with similarity scores
  - Use natural language queries: "authentication bug fixes", "event-driven patterns"

### 💡 Suggested Workflow at Session Start

Before starting work, I refresh context by:

1. **Query recent mental notes** - `query_mental_notes(limit: 20)` to see what I was thinking recently
2. **Search relevant memories** - `semantic_search("recent architecture decisions")` for context
3. **Check project-specific knowledge** - Search for specific topics: "ChromaDB integration", "MCP tools refactoring"
4. **Review session narrative** - Read full session if continuing previous work

### 🔄 During Work

- **Mental notes** → Quick thoughts, decisions, observations as work progresses
- **Memory logs** → Structured documentation of completed solutions, gotchas discovered, patterns learned

### 📝 Pattern

Mental notes capture the **JOURNEY** (chronological, conversational).
Memory logs capture the **DESTINATION** (structured, searchable knowledge).

Both are embedded and searchable, but serve different purposes.

## Common Development Tasks

### Setup
```bash
# Install dependencies
poetry install

# Setup database
poetry run alembic upgrade head
```

### Running the Server
```bash
# Run FastAPI server (port 8000)
poetry run python main.py

# Run MCP server (for Claude Desktop integration)
poetry run python -m src.modules.xcp_server
```

### Database Migrations
```bash
# Create new migration
poetry run alembic revision --autogenerate -m "description"

# Apply migrations
poetry run alembic upgrade head
```

### Testing
```bash
# Run tests
poetry run pytest

# Test specific module
poetry run pytest tests/modules/xcp_server/
```

## Recent Major Work

### Refactoring Marathon
- Modularized XCP server tools (semantic_search, embedding, store_memory, query_mental_notes, store_mental_note)
- Split ChromaDB collection manager into focused modules (cache, operations, manager)
- Created event emitters package with specialized emitters (memory, mental_note, user)
- Built dependency injection module with auto-discovery patterns
- Fixed import errors and moved from inheritance to composition pattern

### Event-Driven Architecture
- Implemented centralized EventBus for pub/sub messaging
- Created event emitters for all major operations
- Added real-time metrics streaming via Socket.IO
- Built ChromaDB metrics collector with performance monitoring

### Multi-Tenant Support
- Added user_id and project_id isolation
- Physical data separation in ChromaDB: `./data/chromadb/{user_id}/{project_id}/`
- Collection naming with SHA256 hashing for security

Ready to continue building! What should we work on next?
