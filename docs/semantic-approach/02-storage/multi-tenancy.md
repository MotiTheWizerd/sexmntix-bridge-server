# Multi-Tenancy Isolation

## Isolation Strategy

Complete data isolation per **user + project** combination.

## How It Works

### 1. Generate Isolation Hash

```python
def generate_collection_hash(user_id: str, project_id: str) -> str:
    data = f"{user_id}:{project_id}"
    hash_full = hashlib.sha256(data.encode()).hexdigest()
    return hash_full[:16]

# Example:
# user_id="user123", project_id="project456"
# → hash="a1b2c3d4e5f6g7h8"
```

### 2. PostgreSQL: Filter by Columns

```sql
SELECT * FROM memory_logs
WHERE user_id = 'user123'
  AND project_id = 'project456';
```

**Isolation**: Query-time filtering
**Performance**: Fast with composite index

### 3. ChromaDB: Separate Collections

```python
collection_name = f"memory_logs_{hash}"
# → "memory_logs_a1b2c3d4e5f6g7h8"

collection = client.get_or_create_collection(collection_name)
```

**Isolation**: Physical separation
**Performance**: No filtering needed

## Tenant Mapping

```
┌─────────────┬──────────────┬──────────────────────┐
│ User ID     │ Project ID   │ ChromaDB Collection  │
├─────────────┼──────────────┼──────────────────────┤
│ user123     │ project456   │ memory_logs_a1b2...  │
│ user123     │ project789   │ memory_logs_c3d4...  │
│ user456     │ project456   │ memory_logs_e5f6...  │
└─────────────┴──────────────┴──────────────────────┘
```

Each combination gets unique collection.

## Benefits

### 1. Complete Isolation
- User A cannot access User B's data
- Project 1 data separate from Project 2
- No risk of data leakage

### 2. Performance
- No need to filter by user_id/project_id in ChromaDB
- Smaller collections = faster queries
- Can optimize per-tenant (different index settings)

### 3. Deletion
- Drop collection to delete all user/project data
- No need to scan and delete individual records

### 4. Scaling
- Can move collections to different ChromaDB instances
- Per-tenant rate limiting
- Independent backup/restore

## Security

### Access Control

```python
def verify_access(user_id: str, project_id: str, requested_user: str, requested_project: str):
    """Verify user can access this tenant data"""
    if user_id != requested_user:
        raise Unauthorized("Cannot access other user's data")

    if project_id != requested_project:
        raise Unauthorized("Cannot access other project's data")
```

### Collection Name Hashing

**Why hash instead of plain user:project?**

1. **Privacy**: Collection names may be logged/visible
2. **Fixed length**: All hashes same size
3. **No special chars**: Avoid issues with `:` in names

**Example**:
```
Bad:  memory_logs_user123:project456
Good: memory_logs_a1b2c3d4e5f6g7h8
```

## Multi-Project Support

### User with Multiple Projects

```python
user_id = "user123"
projects = ["project1", "project2", "project3"]

# Each project gets separate collection
for project_id in projects:
    collection_name = generate_collection_name(user_id, project_id)
    # memory_logs_hash1, memory_logs_hash2, memory_logs_hash3
```

### Cross-Project Search

```python
def search_across_projects(user_id: str, projects: List[str], query: str):
    """Search across multiple user's projects"""
    all_results = []

    for project_id in projects:
        collection_name = generate_collection_name(user_id, project_id)
        results = search_collection(collection_name, query)
        all_results.extend(results)

    # Merge and re-rank
    return sorted(all_results, key=lambda x: x.similarity, reverse=True)
```

## Tenant Management

### Create Tenant

```python
def create_tenant(user_id: str, project_id: str):
    """Initialize tenant resources"""
    # PostgreSQL: No action needed (filtered queries)

    # ChromaDB: Create collection
    collection_name = generate_collection_name(user_id, project_id)
    collection = client.create_collection(collection_name)

    logger.info(f"Created tenant: {user_id}:{project_id}")
```

### Delete Tenant

```python
def delete_tenant(user_id: str, project_id: str):
    """Delete all tenant data"""
    # PostgreSQL: Delete records
    db.query(MemoryLog).filter(
        MemoryLog.user_id == user_id,
        MemoryLog.project_id == project_id
    ).delete()

    # ChromaDB: Drop collection
    collection_name = generate_collection_name(user_id, project_id)
    client.delete_collection(collection_name)

    logger.info(f"Deleted tenant: {user_id}:{project_id}")
```

### List Tenant Collections

```python
def list_tenant_collections(user_id: str) -> List[str]:
    """List all collections for a user"""
    # Query PostgreSQL for unique projects
    projects = db.query(MemoryLog.project_id).filter(
        MemoryLog.user_id == user_id
    ).distinct().all()

    return [generate_collection_name(user_id, p[0]) for p in projects]
```

## Monitoring

### Per-Tenant Metrics

```python
def get_tenant_stats(user_id: str, project_id: str):
    """Get statistics for a tenant"""
    # PostgreSQL count
    pg_count = db.query(MemoryLog).filter(
        MemoryLog.user_id == user_id,
        MemoryLog.project_id == project_id
    ).count()

    # ChromaDB count
    collection_name = generate_collection_name(user_id, project_id)
    collection = client.get_collection(collection_name)
    chroma_count = collection.count()

    return {
        "user_id": user_id,
        "project_id": project_id,
        "postgresql_count": pg_count,
        "chromadb_count": chroma_count,
        "in_sync": pg_count == chroma_count
    }
```

## Best Practices

1. **Always verify access**: Check user_id and project_id before operations
2. **Use consistent hashing**: Same algorithm everywhere
3. **Log tenant operations**: Audit trail for security
4. **Monitor sync status**: Ensure PostgreSQL and ChromaDB counts match
5. **Graceful degradation**: If ChromaDB unavailable, PostgreSQL queries still work

---

*Part of the [Storage Documentation](./README.md)*
