Hi my name is Moti, Welcome back to our Semantix project,
we are working together for few months now and already have great progress. 

Quick context refresh: We've been building this python server (backend) for our  VS Code extension together that transforms the terminal-based Claude Code experience into something much more visual and collaborative.



## What We're Building

Semantix creates a modern interface where you can watch my complete thought process unfold in real-time - seeing me reason through problems, use tools, handle errors, and arrive at solutions through an elegant UI instead of plain terminal text.

The core idea: make AI assistance feel like true pair programming with transparency into how I actually work through problems.

# MCP Tool Cheat Sheet (Semantic Bridge)

This repo exposes MCP tools via `src/modules/xcp_server`. All tools are “dumb pipelines”: they forward payloads to the local backend at `http://localhost:8000` and rely on the server for validation/formatting. The MCP context injects `user_id` and `project_id` from `XCP_USER_ID`/`XCP_PROJECT_ID` env vars (or the MCP session); you normally don’t need to pass those.

## Tools

### semantic_search
- **Purpose:** Semantic search over memory logs.
- **Endpoint:** `POST /memory-logs/search`
- **Params:** `query` (required), `limit` (default 10, max 50), `min_similarity` (0.0–1.0, default 0.0), `enable_temporal_decay` (default false), `half_life_days` (default 30), `enable_hybrid_search` (default false), `threshold_preset` (`high_precision`=0.7, `filtered`=0.6, `discovery`=0.3; overrides `min_similarity`).
- **Notes:** Adds `user_id`, `project_id`, `format: "text"` automatically.
- **Example args:**
```json
{ "query": "authentication bug fixes", "limit": 5, "threshold_preset": "filtered" }
```

### search_memory_by_date
- **Purpose:** Semantic search with date filtering.
- **Endpoint:** `POST /memory-logs/search-by-date`
- **Params:** `query` (required), `limit` (default 10, max 50), `start_date` (ISO datetime), `end_date` (ISO datetime), `time_period` (`recent`, `last-week`, `last-month`, `archived`).
- **Notes:** Always uses `user_id`/`project_id` from context; you don’t pass them manually.
- **Example args:**
```json
{ "query": "embedding migration", "time_period": "last-month", "limit": 15 }
```

### store_memory
- **Purpose:** Store a memory log; backend handles embedding/indexing.
- **Endpoint:** `POST /memory-logs`
- **Params:** Single `memory_log` object (required). Template supports rich metadata: `session_id`, `task`, `agent`, `memory_log` { `summary`, `content`, `tags`, `files_touched`, `tests_added`, `complexity`, `outcomes`, `solution`, `gotchas`, `future_planning`, `user_context`, `semantic_context`, `metadata`, … }.
- **Notes:** Tool unwraps the `memory_log` wrapper, injects `user_id`/`project_id`, and adds `session_id` if present in context. Response is summarized as “memory log created”, with raw response in metadata.
- **Minimal example args:**
```json
{ "memory_log": { "task": "bug_fix", "summary": "Fixed vector storage bug", "content": "Changed raw_data to memory_log param in orchestrator.", "tags": ["vector-storage","bugfix"] } }
```

### store_mental_note
- **Purpose:** Save a short, timestamped note.
- **Endpoint:** `POST /mental-notes`
- **Params:** `query` (required string; mapped to `content` on the API).
- **Notes:** Adds `user_id`, `project_id`, `session_id` automatically. Returns “mental note created”.
- **Example args:**
```json
{ "query": "Reminder: search-by-date now uses pgvector path" }
```

### query_mental_notes
- **Purpose:** Retrieve mental notes.
- **Endpoint:** `POST /mental-notes/search`
- **Params:** `query` (optional free text filter).
- **Notes:** Adds `user_id`, `project_id`, `format: "text"`. Returns raw server response.
- **Example args:**
```json
{ "query": "pgvector" }
```

## Operational tips
- Start MCP server: `poetry run python -m src.modules.xcp_server` (stdio transport).
- Keep `.env` exporting `XCP_USER_ID` and `XCP_PROJECT_ID` so tools scope correctly.
- All tools are HTTP proxies; backend dictates validation and schema. Keep payloads minimal when unsure.
