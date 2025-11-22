"""
Search memory by date tool configuration
"""

from src.modules.xcp_server.tools.base.models import ToolDefinition, ToolParameter

SEARCH_MEMORY_BY_DATE_TOOL_DEF = ToolDefinition(
    name="search_memory_by_date",
    description=(
        "Search through stored memories using semantic similarity with date filtering. "
        "Provide a natural language query and get back the most relevant memories from a specific time period. "
        "Supports both explicit date ranges (start_date/end_date) and convenience time period shortcuts "
        "(recent, last-week, last-month, archived)."
    ),
    parameters=[
        ToolParameter(
            name="user_id",
            type="string",
            description="User ID for scoping the search (required)",
            required=True
        ),
        ToolParameter(
            name="project_id",
            type="string",
            description="Project ID for scoping the search (required)",
            required=True
        ),
        ToolParameter(
            name="query",
            type="string",
            description="The search query in natural language (e.g., 'authentication bug fixes', 'database optimization tips')",
            required=True
        ),
        ToolParameter(
            name="limit",
            type="number",
            description="Maximum number of results to return (default: 10, max: 50)",
            required=False
        ),
        ToolParameter(
            name="start_date",
            type="string",
            description="Start date filter in ISO datetime format (e.g., '2024-01-01T00:00:00'). Optional if using time_period.",
            required=False
        ),
        ToolParameter(
            name="end_date",
            type="string",
            description="End date filter in ISO datetime format (e.g., '2024-12-31T23:59:59'). Optional if using time_period.",
            required=False
        ),
        ToolParameter(
            name="time_period",
            type="string",
            description="Convenience time period filter. Options: 'recent' (last 7 days), 'last-week' (last 7 days), 'last-month' (last 30 days), 'archived' (older than 30 days). Overrides start_date/end_date if provided.",
            required=False
        ),
    ]
)
