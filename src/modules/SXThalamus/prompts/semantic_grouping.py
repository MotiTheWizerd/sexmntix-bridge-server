"""
Semantic grouping prompt for analyzing AI conversations and creating memory units.
"""


def build_semantic_grouping_prompt(conversation_text: str) -> str:
    """
    Build a prompt for semantic grouping of conversation content.

    Args:
        conversation_text: The conversation text to analyze and group into semantic chunks

    Returns:
        Formatted prompt string for the AI model
    """
    return f"""You are a memory creation expert. Your task is to analyze AI-human conversations and group related exchanges into meaningful semantic chunks called "memory units."

**Instructions:**
1. Read through the entire conversation carefully
2. Identify natural topic boundaries and thematic shifts
3. Group related exchanges (question-answer pairs, multi-turn discussions) into memory units
4. Create a unique memory_id and group_id for each unit
5. For each memory unit, provide:
   - A clear topic/title
   - A concise summary of what was discussed
   - Your reflection on why this is significant (think like an AI assistant reviewing its own conversation)
   - Key technical points, decisions, or insights
   - Relevant tags for searchability
   - Related topics that might connect to other memories

**Important Guidelines:**
- A memory unit should represent ONE coherent topic or task
- Multi-turn exchanges on the same topic belong in the same unit
- Quick back-and-forth clarifications belong with their main topic
- Each unit should be self-contained enough to be understood independently
- Use natural, conversational language in your reflections
- Think reflectively: "I notice...", "This reminds me...", "The user wanted..."

**Example Output Format:**

```json
[
  {{
    "memory_id": "mem_001",
    "group_id": "grp_dark_mode_feature",
    "topic": "Implementing Dark Mode Toggle",
    "summary": "User requested adding a dark mode toggle to application settings. We discussed the implementation approach including UI component, state management, and CSS-in-JS styling.",
    "reflection": "I notice this was a well-scoped feature request. The user wanted a complete dark mode implementation, not just a theme switcher. This reminds me that UI state management is a recurring pattern in this codebase - we consistently use React Context for app-wide settings.",
    "key_points": [
      "Created toggle component in Settings page",
      "Implemented theme context for global state",
      "Used CSS-in-JS for dynamic theme switching",
      "Ensured all components support both themes"
    ],
    "metadata": {{
      "feature_type": "UI enhancement",
      "complexity": "medium",
      "involves_state_management": true
    }},
    "tags": ["dark-mode", "theming", "settings", "UI", "state-management"],
    "related_topics": ["theme-context", "CSS-in-JS", "settings-page"],
    "timestamp": "2025-01-15T10:30:00Z"
  }},
  {{
    "memory_id": "mem_002",
    "group_id": "grp_dark_mode_feature",
    "topic": "Dark Mode Testing and Bug Fixes",
    "summary": "After implementation, we discovered the navbar wasn't respecting the theme. Fixed by ensuring the Navbar component consumed the theme context.",
    "reflection": "This is a common pattern I see - initial implementations often miss edge cases in shared components. The user caught this quickly during testing, which shows good attention to detail. The fix was straightforward once we identified the root cause.",
    "key_points": [
      "Bug: Navbar component not using theme context",
      "Root cause: Component wasn't wrapped in ThemeProvider",
      "Solution: Added theme context consumption to Navbar",
      "Verified all shared components now support theming"
    ],
    "metadata": {{
      "issue_type": "bug_fix",
      "complexity": "low",
      "related_to": "mem_001"
    }},
    "tags": ["bug-fix", "dark-mode", "navbar", "theme-context"],
    "related_topics": ["component-architecture", "theme-context", "shared-components"],
    "timestamp": "2025-01-15T11:15:00Z"
  }}
]
```

**Now analyze this conversation:**

{conversation_text}

**Output only the JSON array of memory units. No additional text before or after the JSON.**"""
