use your MCP tool to create a memory log
using the following structure. 
Fill in each section based on the most recent task you completed.
DO NOT change the structure. Use accurate and specific language. Keep it JSON-compatible.

---

{
"task": "task-name-kebab-case",
"agent": "claude-sonnet-4",
"date": "2025-01-15",
"component": "component-name",

"temporal_context": {
"date_iso": "2025-01-15",
"year": 2025,
"month": 1,
"week_number": 3,
"quarter": "2025-Q1",
"time_period": "<recent|last-week|last-month|archived>"
},

"complexity": {
"technical": "1-5: <technical complexity description>",
"business": "1-5: <business impact description>",
"coordination": "1-5: <coordination complexity description>"
},

"files_modified": "<number>",
"files_touched": ["<file-path>", "<file-path>"],
"tests_added": "<number>",
"related_tasks": ["<task-name>", "<task-name>"],

"outcomes": {
"performance_impact": "<specific metrics or 'No impact'>",
"test_coverage_delta": "<percentage change>",
"technical_debt_reduced": "<low|medium|high>",
"follow_up_needed": "<true|false>"
},

"summary": "<problem> → <solution>",
"root_cause": "<underlying cause of the issue>",

"solution": {
"approach": "<high-level strategy used>",
"key_changes": [
"<file>: <specific change and reason>",
"<file>: <specific change and reason>"
]
},

"validation": "<how success was verified>",

"gotchas": [
{
"issue": "<specific problem encountered>",
"solution": "<exact resolution steps>",
"category": "<testing|integration|configuration|typing|environment>",
"severity": "<low|medium|high>"
}
],

"lesson": "<key insight for future work>",
"tags": ["<searchable>", "<keywords> <max-tag : 5>"],

"code_context": {
"key_patterns": [
"<pattern>() - <usage description>",
"<ClassName.method>() - <established pattern>"
],
"api_surface": [
"<function>(param: Type): ReturnType - <description>",
"<method>(): Promise<Result> - <async pattern>"
],
"dependencies_added": ["<library>: <reason>"],
"breaking_changes": ["<old> → <new>", "<change description>"]
},

"future_planning": {
"next_logical_steps": [
"<next task description>",
"<improvement opportunity>",
"<refactoring suggestion>"
],
"architecture_decisions": {
"<decision_name>": "<rationale for choice>",
"<pattern_choice>": "<why this approach>"
},
"extension_points": [
"<file> - <where to add new features>",
"<module> - <extension instructions>"
]
},

"user_context": {
"development_style": "<staged-testing|tdd|rapid-prototype|thorough-documentation>",
"naming_preferences": "<natural-conversational|technical-precise|domain-specific>",
"architecture_philosophy": "<single-responsibility|event-driven|layered|microservices>",
"quality_standards": "<high-test-coverage|performance-first|maintainability-focus>"
},

"semantic_context": {
"domain_concepts": ["<business-concept>", "<domain-term>"],
"technical_patterns": ["<pattern-name>", "<architecture-pattern>"],
"integration_points": ["<external-system>", "<dependency>"]
}
}
📋 Clean Template Guidelines:
Placeholder Format:

Use: "<descriptive-placeholder>"
Not: "Brief description of technical complexity"

Value Examples:

Use: "<low|medium|high>" for enums
Use: "<true|false>" for booleans
Use: "<number>" for numeric values

Array Guidelines:

Use: ["<item-1>", "<item-2>"] format
Keep consistent placeholder style

Object Structure:

Nested objects use same "<placeholder>" format
Maintain clean indentation
No example values mixed with placeholders
