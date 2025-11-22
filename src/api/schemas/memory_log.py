from pydantic import BaseModel, field_validator
from datetime import datetime, date
from typing import Dict, Any, Optional, List, Literal, Union


# ============================================================================
# Nested Schema Models
# ============================================================================

class TemporalContext(BaseModel):
    """Temporal context information"""
    date_iso: str  # ISO format date string
    year: int
    month: int
    week_number: int
    quarter: str  # e.g., "2025-Q1"
    time_period: Literal["recent", "last-week", "last-month", "archived"]


class Complexity(BaseModel):
    """Complexity metrics"""
    technical: Optional[str] = None  # "1-5: <description>"
    business: Optional[str] = None  # "1-5: <description>"
    coordination: Optional[str] = None  # "1-5: <description>"


class Outcomes(BaseModel):
    """Outcome metrics"""
    performance_impact: Optional[str] = None  # "<specific metrics or 'No impact'>"
    test_coverage_delta: Optional[str] = None  # "<percentage change>"
    technical_debt_reduced: Optional[str] = None  # Accept any string value
    follow_up_needed: Optional[bool] = None


class Solution(BaseModel):
    """Solution details"""
    approach: Optional[str] = None  # "<high-level strategy used>"
    key_changes: Optional[List[str]] = None  # ["<file>: <specific change and reason>"]


class Gotcha(BaseModel):
    """Gotcha/issue encountered"""
    issue: Optional[str] = None  # "<specific problem encountered>"
    solution: Optional[str] = None  # "<exact resolution steps>"
    category: Optional[str] = None  # Accept any string value
    severity: Optional[str] = None  # Accept any string value


class CodeContext(BaseModel):
    """Code context information"""
    key_patterns: Optional[List[str]] = None  # ["<pattern>() - <usage description>"]
    api_surface: Optional[List[str]] = None  # ["<function>(param: Type): ReturnType - <description>"]
    dependencies_added: Optional[List[str]] = None  # ["<library>: <reason>"]
    breaking_changes: Optional[List[str]] = None  # ["<old> → <new>", "<change description>"]


class FuturePlanning(BaseModel):
    """Future planning information"""
    next_logical_steps: Optional[List[str]] = None  # ["<next task description>"]
    architecture_decisions: Optional[Dict[str, str]] = None  # {"<decision_name>": "<rationale>"}
    extension_points: Optional[List[str]] = None  # ["<file> - <where to add new features>"]


class UserContext(BaseModel):
    """User context preferences"""
    development_style: Optional[str] = None  # "<staged-testing|tdd|rapid-prototype|thorough-documentation>"
    naming_preferences: Optional[str] = None  # "<natural-conversational|technical-precise|domain-specific>"
    architecture_philosophy: Optional[str] = None  # "<single-responsibility|event-driven|layered|microservices>"
    quality_standards: Optional[str] = None  # "<high-test-coverage|performance-first|maintainability-focus>"


class SemanticContext(BaseModel):
    """Semantic context information"""
    domain_concepts: Optional[List[str]] = None  # ["<business-concept>", "<domain-term>"]
    technical_patterns: Optional[List[str]] = None  # ["<pattern-name>", "<architecture-pattern>"]
    integration_points: Optional[List[str]] = None  # ["<external-system>", "<dependency>"]


# ============================================================================
# Main Memory Log Schema
# ============================================================================

class MemoryLogData(BaseModel):
    """
    Memory log data structure.
    
    Note: task, agent, date, and temporal_context are now stored as top-level columns,
    not in this JSON structure. This contains only the actual memory content.
    """
    # Optional core fields
    component: Optional[str] = None  # "component-name"
    complexity: Optional[Complexity] = None
    files_modified: Optional[Union[str, int]] = None  # Accept both string and int
    files_touched: Optional[List[str]] = None  # ["<file-path>"]
    tests_added: Optional[Union[str, int]] = None  # Accept both string and int
    related_tasks: Optional[List[str]] = None  # ["<task-name>"]
    outcomes: Optional[Outcomes] = None
    summary: Optional[str] = None  # "<problem> → <solution>"
    root_cause: Optional[str] = None  # "<underlying cause of the issue>"
    solution: Optional[Solution] = None
    validation: Optional[str] = None  # "<how success was verified>"
    gotchas: Optional[List[Gotcha]] = None
    lesson: Optional[str] = None  # "<key insight for future work>"
    tags: Optional[List[str]] = None  # ["<searchable>", "<keywords>"]
    code_context: Optional[CodeContext] = None
    future_planning: Optional[FuturePlanning] = None
    user_context: Optional[UserContext] = None
    semantic_context: Optional[SemanticContext] = None
    
    # Legacy support
    content: Optional[str] = None  # For backward compatibility
    metadata: Optional[Dict[str, Any]] = {}  # For backward compatibility
    
    model_config = {"extra": "allow"}


class MemoryLogCreate(BaseModel):
    """
    Simplified format for memory log creation
    
    Format:
    {
        "user_id": "uuid-string",
        "project_id": "default",
        "session_id": "string",
        "task": "task-name-kebab-case",
        "agent": "claude-sonnet-4", 
        "memory_log": {
            "component": "...",
            "summary": "...",
            ... (all fields optional)
        }
    }
    
    The system will automatically:
    - Set created_at timestamp automatically
    """
    user_id: str
    project_id: str
    session_id: Optional[str] = None
    task: str
    agent: str
    memory_log: MemoryLogData


class MemoryLogResponse(BaseModel):
    id: str
    task: str
    agent: str
    session_id: Optional[str] = None
    memory_log: Dict[str, Any]
    embedding: Optional[List[float]] = None
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MemoryLogSearchRequest(BaseModel):
    query: str
    user_id: str  # Required: UUID from users table
    project_id: Optional[str] = "default"  # Default project_id if not provided
    limit: Optional[int] = 10
    min_similarity: Optional[float] = 0.0
    filters: Optional[Dict[str, Any]] = None
    tag: Optional[str] = None  # Filter by individual tag (e.g., "chromadb")


class MemoryLogSearchResult(BaseModel):
    id: str
    memory_log_id: Optional[str] = None
    document: Dict[str, Any]
    metadata: Dict[str, Any]
    distance: float
    similarity: float


class MemoryLogDateSearchRequest(BaseModel):
    """
    Search memory logs with date filtering

    Supports both explicit date ranges and convenience time period shortcuts.
    """
    user_id: str  # Required: UUID from users table
    project_id: str  # Required: Project identifier
    query: str  # Search query text
    limit: Optional[int] = 10  # Max results to return
    start_date: Optional[datetime] = None  # Start date filter (ISO format)
    end_date: Optional[datetime] = None  # End date filter (ISO format)
    time_period: Optional[Literal["recent", "last-week", "last-month", "archived"]] = None  # Convenience shortcuts
