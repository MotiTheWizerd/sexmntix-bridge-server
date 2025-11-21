# PostgreSQL with pgvector

## Schema

### memory_logs Table

```sql
CREATE TABLE memory_logs (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    project_id VARCHAR(255) NOT NULL,
    raw_data JSONB NOT NULL,
    embedding VECTOR(768),  -- pgvector extension
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_memory_logs_user_project
    ON memory_logs(user_id, project_id);

CREATE INDEX idx_memory_logs_created_at
    ON memory_logs(created_at DESC);

-- pgvector index for similarity search (optional, ChromaDB is primary)
CREATE INDEX idx_memory_logs_embedding
    ON memory_logs
    USING ivfflat (embedding vector_l2_ops)
    WITH (lists = 100);
```

## Fields

| Field | Type | Purpose |
|-------|------|---------|
| `id` | SERIAL | Primary key |
| `user_id` | VARCHAR | Tenant isolation |
| `project_id` | VARCHAR | Tenant isolation |
| `raw_data` | JSONB | Full memory content |
| `embedding` | VECTOR(768) | Backup of embedding |
| `created_at` | TIMESTAMP | Creation time |
| `updated_at` | TIMESTAMP | Last update |

## Why JSONB for raw_data?

**Benefits**:
- Flexible schema
- Store any memory structure
- Query nested fields
- Index specific paths

**Example**:
```sql
-- Query memories with specific tag
SELECT * FROM memory_logs
WHERE raw_data->'tags' ? 'authentication';

-- Query by nested field
SELECT * FROM memory_logs
WHERE raw_data->>'component' = 'auth-service';
```

## pgvector Extension

### What is pgvector?

PostgreSQL extension for vector similarity search.

### Why Store Embeddings Here?

1. **Backup**: If ChromaDB data lost, can rebuild
2. **Audit**: Track embedding changes over time
3. **Fallback**: Can query PostgreSQL if ChromaDB down
4. **Analytics**: Join with other tables for analysis

### Similarity Query (Optional)

```sql
-- Find similar memories using PostgreSQL
SELECT id, raw_data,
       1 - (embedding <-> :query_embedding) AS similarity
FROM memory_logs
WHERE user_id = :user_id
  AND project_id = :project_id
ORDER BY embedding <-> :query_embedding
LIMIT 10;
```

**Note**: ChromaDB is faster, use PostgreSQL only as fallback.

## Isolation Strategy

### Query Pattern

Always filter by user_id and project_id:

```python
memories = db.query(MemoryLog).filter(
    MemoryLog.user_id == user_id,
    MemoryLog.project_id == project_id
).all()
```

### Index Performance

```sql
-- Index ensures fast filtering
EXPLAIN ANALYZE
SELECT * FROM memory_logs
WHERE user_id = 'user123'
  AND project_id = 'project456';

-- Should use: idx_memory_logs_user_project
-- Execution time: ~1-5ms
```

## Common Queries

### Create Memory

```sql
INSERT INTO memory_logs (user_id, project_id, raw_data)
VALUES (:user_id, :project_id, :raw_data::jsonb)
RETURNING id;
```

### Update Embedding

```sql
UPDATE memory_logs
SET embedding = :embedding,
    updated_at = NOW()
WHERE id = :memory_id;
```

### Get Memory by ID

```sql
SELECT * FROM memory_logs
WHERE id = :memory_id
  AND user_id = :user_id
  AND project_id = :project_id;
```

### Delete Memory

```sql
DELETE FROM memory_logs
WHERE id = :memory_id
  AND user_id = :user_id
  AND project_id = :project_id;
```

### List Memories

```sql
SELECT * FROM memory_logs
WHERE user_id = :user_id
  AND project_id = :project_id
ORDER BY created_at DESC
LIMIT 20 OFFSET 0;
```

## Backup & Recovery

### Backup Strategy

```bash
# Full backup
pg_dump semantix_db > backup.sql

# Table-specific backup
pg_dump -t memory_logs semantix_db > memory_logs_backup.sql

# Compressed backup
pg_dump semantix_db | gzip > backup.sql.gz
```

### Restore

```bash
# Full restore
psql semantix_db < backup.sql

# Table-specific restore
psql semantix_db < memory_logs_backup.sql
```

---

*Part of the [Storage Documentation](./README.md)*
