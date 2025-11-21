# Text Extraction for Embeddings

## Overview

Memory logs are structured data. Before embedding, we extract a searchable text representation combining all relevant fields.

## Extraction Strategy

### Input: Structured Memory

```json
{
    "task": "Fix authentication bug",
    "summary": "Users couldn't log in with special characters in password",
    "solution": "Added input sanitization to login form",
    "component": "auth-service",
    "tags": ["bug", "security", "authentication"],
    "root_cause": "Regex validation was too strict"
}
```

### Output: Searchable Text

```
Task: Fix authentication bug

Summary: Users couldn't log in with special characters in password

Solution: Added input sanitization to login form

Component: auth-service

Tags: bug, security, authentication

Root Cause: Regex validation was too strict
```

## Why This Format?

1. **Semantic richness**: Includes all context for better embeddings
2. **Field labels**: "Task:", "Summary:" help model understand structure
3. **Natural language**: Reads like human description
4. **Comprehensive**: Nothing important is omitted

## Field Importance

### High Importance (Always Include)
- **task**: What was done
- **summary**: Detailed description
- **solution**: How it was solved
- **tags**: Keywords for categorization

### Medium Importance (Include if Present)
- **component**: Which part of system
- **root_cause**: Why issue occurred
- **lesson_learned**: Key takeaway
- **outcome**: Result of action

## Best Practices

1. **Include all relevant fields**: Don't skip important context
2. **Use field labels**: "Task:", "Summary:" help structure
3. **Handle missing data**: Graceful fallbacks
4. **Preserve semantic meaning**: Keep natural language
5. **Consistent format**: Same extraction logic everywhere

---

*Part of the [Storage Documentation](./README.md)*
