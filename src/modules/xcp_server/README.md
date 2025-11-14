# XCP Server Module

> **MCP (Model Context Protocol) Server for Semantic Bridge**

The XCP Server module exposes Semantic Bridge's semantic memory and vector storage capabilities to AI assistants through the standardized Model Context Protocol (MCP). This allows AI assistants like Claude to search, store, and retrieve memories using natural language.

## 🌟 Features

- **5 MCP Tools** for AI assistant interaction
- **Vector Semantic Search** using embeddings
- **Automatic Memory Indexing** with ChromaDB
- **Mental Notes** for session tracking
- **Event-Driven Architecture** for real-time updates
- **Multi-User/Project Isolation** for data security
- **Stdio Transport** for local AI assistant integration

## 🛠️ Available Tools

### 1. **semantic_search**
Search through stored memories using semantic similarity.

**Parameters:**
- `query` (string, required): Natural language search query
- `limit` (number, optional): Max results (default: 10, max: 50)
- `min_similarity` (number, optional): Similarity threshold 0.0-1.0 (default: 0.0)
- `user_id` (number, optional): Override default user ID
- `project_id` (string, optional): Override default project ID

**Example:**
```json
{
  "query": "authentication bug fixes",
  "limit": 5,
  "min_similarity": 0.7
}
```

### 2. **store_memory**
Store a new memory log with automatic vector embedding.

**Parameters:**
- `content` (string, required): Memory content
- `task` (string, required): Task/category (e.g., 'bug_fix', 'learning')
- `agent` (string, optional): Source agent (default: 'mcp_client')
- `tags` (array, optional): Up to 5 tags for categorization
- `metadata` (object, optional): Additional key-value metadata
- `user_id` (number, optional): Override default user ID
- `project_id` (string, optional): Override default project ID

**Example:**
```json
{
  "content": "Fixed authentication timeout issue by increasing session TTL",
  "task": "bug_fix",
  "tags": ["authentication", "session", "bugfix"],
  "metadata": {
    "severity": "high",
    "component": "auth-module"
  }
}
```

### 3. **generate_embedding**
Generate a vector embedding for text.

**Parameters:**
- `text` (string, required): Text to embed
- `return_full_vector` (boolean, optional): Return complete vector (default: false)

**Example:**
```json
{
  "text": "How to implement JWT authentication in FastAPI",
  "return_full_vector": false
}
```

### 4. **store_mental_note**
Store a mental note (timestamped observation).

**Parameters:**
- `content` (string, required): Note content
- `session_id` (string, optional): Session identifier
- `note_type` (string, optional): Note category (default: 'note')
- `metadata` (object, optional): Additional metadata

**Example:**
```json
{
  "content": "User prefers TypeScript over JavaScript",
  "session_id": "session_2024_01_15",
  "note_type": "preference"
}
```

### 5. **query_mental_notes**
Query and retrieve mental notes.

**Parameters:**
- `session_id` (string, optional): Filter by session
- `mental_note_id` (number, optional): Retrieve specific note
- `limit` (number, optional): Max results (default: 50, max: 200)

**Example:**
```json
{
  "session_id": "session_2024_01_15",
  "limit": 20
}
```

## 📦 Installation

### 1. Install Dependencies

```bash
# Install MCP SDK and other dependencies
pip install -e .
```

### 2. Configure Environment

Add the following to your `.env` file:

```bash
# XCP Server Configuration
XCP_SERVER_ENABLED=true
XCP_SERVER_NAME=semantic-bridge-mcp
XCP_SERVER_VERSION=1.0.0
XCP_TRANSPORT=stdio
XCP_DEFAULT_USER_ID=1
XCP_DEFAULT_PROJECT_ID=default
XCP_LOG_LEVEL=info

# Required: Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/semantix-bridge-db

# Required: Embeddings Configuration
GOOGLE_API_KEY=your_google_api_key_here
EMBEDDING_MODEL=models/text-embedding-004

# Required: ChromaDB Configuration
CHROMADB_PATH=./data/chromadb
```

### 3. Database Setup

Ensure your database is set up and migrations are run:

```bash
alembic upgrade head
```

## 🚀 Usage

### Running as Standalone Server

The recommended way to run the XCP server:

```bash
python -m src.modules.xcp_server
```

This starts the server with stdio transport, ready to accept MCP connections.

### Integrating with Claude Desktop

1. **Locate Claude Desktop Config**

   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

2. **Add XCP Server Configuration**

```json
{
  "mcpServers": {
    "semantic-bridge": {
      "command": "python",
      "args": [
        "-m",
        "src.modules.xcp_server"
      ],
      "cwd": "C:/projects/semantic-bridge/sexmntix-bridge-server",
      "env": {
        "PYTHONPATH": "C:/projects/semantic-bridge/sexmntix-bridge-server"
      }
    }
  }
}
```

3. **Restart Claude Desktop**

4. **Verify Connection**

   Open Claude Desktop and look for the hammer icon (🔨) in the message input area. Click it to see available tools.

### Using in Your Application

You can also integrate XCP server into your FastAPI application:

```python
from src.modules.xcp_server import XCPServerService

# In your application lifespan/startup:
xcp_service = XCPServerService(
    event_bus=event_bus,
    logger=logger,
    embedding_service=embedding_service,
    vector_storage_service=vector_storage_service,
    db_session_factory=db_session_factory
)

xcp_service.initialize()

# Optional: Run as background task
await xcp_service.start_background()

# On shutdown:
await xcp_service.stop()
```

## 📊 Architecture

```
┌─────────────────────────────────────────────────┐
│          AI Assistant (Claude)                  │
│              via MCP Protocol                   │
└────────────────┬────────────────────────────────┘
                 │ stdio
                 ↓
┌─────────────────────────────────────────────────┐
│          XCPMCPServer (Protocol Layer)          │
│        Handles MCP tool registration            │
│        and message routing                      │
└────────────────┬────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────┐
│       XCPServerService (Orchestration)          │
│    Coordinates tools and dependencies           │
└────────┬───────┬────────┬────────┬──────────────┘
         │       │        │        │
         ↓       ↓        ↓        ↓
    ┌────────┬────────┬────────┬────────┐
    │ Search │ Store  │Embedding│Notes   │
    │  Tool  │  Tool  │  Tool   │ Tools  │
    └────┬───┴────┬───┴────┬────┴────┬───┘
         │        │        │         │
         ↓        ↓        ↓         ↓
    ┌────────────────────────────────────┐
    │     Core Services & Storage        │
    │  - VectorStorageService            │
    │  - EmbeddingService                │
    │  - PostgreSQL (memories & notes)   │
    │  - ChromaDB (vector search)        │
    └────────────────────────────────────┘
```

## 🔧 Configuration

All configuration is loaded from environment variables:

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `XCP_SERVER_ENABLED` | Enable/disable XCP server | `true` | No |
| `XCP_SERVER_NAME` | Server name for MCP | `semantic-bridge-mcp` | No |
| `XCP_SERVER_VERSION` | Server version | `1.0.0` | No |
| `XCP_TRANSPORT` | Transport type (stdio/sse) | `stdio` | No |
| `XCP_DEFAULT_USER_ID` | Default user ID | `1` | No |
| `XCP_DEFAULT_PROJECT_ID` | Default project ID | `default` | No |
| `XCP_LOG_LEVEL` | Log level | `info` | No |
| `DATABASE_URL` | PostgreSQL connection URL | - | Yes |
| `GOOGLE_API_KEY` | Google API key for embeddings | - | Yes |
| `CHROMADB_PATH` | ChromaDB storage path | `./data/chromadb` | No |

## 📝 Example Usage with Claude

Once configured, you can use these tools naturally in Claude:

**User:** "Search my memories for anything related to authentication bugs"

**Claude:** *Uses semantic_search tool*
```
{
  "query": "authentication bugs",
  "limit": 5,
  "min_similarity": 0.7
}
```

**User:** "Remember that we decided to use JWT tokens with 24-hour expiry"

**Claude:** *Uses store_memory tool*
```
{
  "content": "Team decided to use JWT tokens with 24-hour expiration for authentication",
  "task": "decision",
  "tags": ["authentication", "jwt", "security"]
}
```

## 🧪 Testing

Test the XCP server manually:

```bash
# Start the server
python -m src.modules.xcp_server

# In another terminal, test with MCP Inspector (if available)
# or connect via Claude Desktop
```

## 🐛 Troubleshooting

### Server Won't Start

1. **Check if enabled:**
   ```bash
   # In .env
   XCP_SERVER_ENABLED=true
   ```

2. **Verify dependencies:**
   ```bash
   pip install mcp
   ```

3. **Check logs:**
   Server logs are written to stdout. Set `XCP_LOG_LEVEL=debug` for detailed logs.

### Claude Desktop Can't Connect

1. **Verify config path:** Make sure `cwd` points to your project root
2. **Check PYTHONPATH:** Ensure Python can find your modules
3. **Restart Claude Desktop:** Configuration changes require a restart
4. **Check logs:** Look for XCP server startup messages

### Tools Not Showing Up

1. **Check initialization:** Ensure all 5 tools are registered
2. **Verify MCP protocol:** Check for protocol errors in logs
3. **Test tool definitions:** Each tool should have valid schema

### Database Errors

1. **Run migrations:** `alembic upgrade head`
2. **Check connection:** Verify `DATABASE_URL` is correct
3. **Test connectivity:** Try connecting with psql or pgAdmin

## 📚 Further Reading

- [MCP Documentation](https://modelcontextprotocol.io/)
- [Claude Desktop Integration Guide](https://docs.anthropic.com/claude/docs)
- [Semantic Bridge Architecture](../../README.md)

## 🤝 Contributing

When adding new tools:

1. Extend `BaseTool` class in `tools/`
2. Implement `get_definition()` and `execute()`
3. Register in `XCPServerService._initialize_tools()`
4. Add tests and documentation
5. Update this README

## 📄 License

See main project LICENSE file.
