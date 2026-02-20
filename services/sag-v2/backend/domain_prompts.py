"""
SAG v2 — Domain Prompts + Tool Definitions
=============================================
System prompt for resource allocation assistant.
Tool definitions in OpenAI function-calling format for LLM consumption.
"""

SYSTEM_PROMPT = """You are SAG (Solution Architects Group) Assistant — an AI-powered resource allocation and project management assistant.

You help Solution Architects teams manage their people, projects, and workload using data from Productive and Smartsheet Resource Management.

## Your Capabilities
- Look up team members and their details
- Check availability and utilization for any person or team
- View project assignments and bookings
- Analyze time entries and workload distribution
- Cross-reference data between Productive and Smartsheet for the most accurate picture

## Response Guidelines
1. Always use the available tools to get real data — never guess or make up numbers
2. When asked about availability, check BOTH Productive bookings and Smartsheet availabilities for accuracy
3. Present data in clean, readable tables when showing multiple records
4. Calculate utilization as: (booked_hours / total_capacity) × 100%
5. For date ranges, default to the next 2 weeks unless specified otherwise
6. If a query is ambiguous, ask for clarification rather than guessing
7. Proactively suggest insights — e.g., "Bob is at 120% utilization next week, consider redistributing"

## Data Sources
- **Productive**: Bookings, projects, project assignments, time entries, people profiles
- **Smartsheet RM**: Users, native availability data, assignments, time entries

When both sources have overlapping data (e.g., availability), prefer Smartsheet's native availability endpoint as it accounts for holidays and custom schedules.
"""


def build_tool_definitions() -> list:
    """Return tool definitions in OpenAI function-calling format."""
    return [
        # --- Productive Tools ---
        {
            "type": "function",
            "function": {
                "name": "list_people",
                "description": "List team members from Productive. Filter by status (active/archived) or search by name.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "description": "active or archived", "default": "active"},
                        "search": {"type": "string", "description": "Search by name"},
                        "page_size": {"type": "integer", "default": 50},
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_person_details",
                "description": "Get detailed info about a person including their project assignments.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "person_id": {"type": "string", "description": "Productive person ID"},
                    },
                    "required": ["person_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_bookings",
                "description": "List resource bookings (scheduled work) from Productive. Filter by date range, person, or project.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "date_after": {"type": "string", "description": "Start date YYYY-MM-DD"},
                        "date_before": {"type": "string", "description": "End date YYYY-MM-DD"},
                        "person_id": {"type": "string"},
                        "project_id": {"type": "string"},
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_availability",
                "description": "Calculate a person's availability from Productive bookings. Shows booked vs capacity per day.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "person_id": {"type": "string", "description": "Productive person ID"},
                        "date_from": {"type": "string", "description": "Start date YYYY-MM-DD"},
                        "date_to": {"type": "string", "description": "End date YYYY-MM-DD"},
                        "daily_capacity": {"type": "number", "default": 8},
                    },
                    "required": ["person_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_projects_productive",
                "description": "List projects from Productive.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "status": {"type": "string", "default": "active"},
                        "search": {"type": "string"},
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_project_assignments",
                "description": "List who is assigned to which project in Productive.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "person_id": {"type": "string"},
                        "project_id": {"type": "string"},
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_time_entries_productive",
                "description": "Get time tracking entries from Productive for a person or project.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "person_id": {"type": "string"},
                        "project_id": {"type": "string"},
                        "date_after": {"type": "string"},
                        "date_before": {"type": "string"},
                    },
                },
            },
        },
        # --- Smartsheet RM Tools ---
        {
            "type": "function",
            "function": {
                "name": "list_users",
                "description": "List team members from Smartsheet Resource Management.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "role": {"type": "string"},
                        "per_page": {"type": "integer", "default": 50},
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_user_availability",
                "description": "Get a user's availability from Smartsheet RM (native endpoint — most accurate, includes holidays).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string", "description": "Smartsheet RM user ID"},
                        "from_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                        "to_date": {"type": "string", "description": "End date YYYY-MM-DD"},
                    },
                    "required": ["user_id"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_projects_smartsheet",
                "description": "List projects from Smartsheet Resource Management.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filter_field": {"type": "string"},
                        "filter_value": {"type": "string"},
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_assignments",
                "description": "List assignments from Smartsheet RM — who is assigned to what.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "project_id": {"type": "string"},
                        "from_date": {"type": "string"},
                        "to_date": {"type": "string"},
                    },
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_time_entries_smartsheet",
                "description": "Get time entries from Smartsheet RM.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {"type": "string"},
                        "project_id": {"type": "string"},
                        "from_date": {"type": "string"},
                        "to_date": {"type": "string"},
                    },
                },
            },
        },
    ]