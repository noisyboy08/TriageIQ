from config import CATEGORIES, PRIORITIES, TEAMS

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "name": "categorize_ticket",
        "description": "Assign a category to the support ticket.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": CATEGORIES,
                    "description": "The category that best describes this ticket.",
                },
                "reasoning": {
                    "type": "string",
                    "description": "One sentence explaining why this category was chosen.",
                },
            },
            "required": ["category", "reasoning"],
        },
    },
    {
        "type": "function",
        "name": "set_priority",
        "description": "Assign a priority level to the ticket based on business impact and urgency.",
        "parameters": {
            "type": "object",
            "properties": {
                "priority": {
                    "type": "string",
                    "enum": PRIORITIES,
                    "description": "CRITICAL = service down / data loss / security breach. HIGH = major feature broken, many users affected. MEDIUM = partial issue, workaround exists. LOW = minor, cosmetic, or informational.",
                },
                "justification": {
                    "type": "string",
                    "description": "Why this priority level was assigned.",
                },
                "sla_hours": {
                    "type": "integer",
                    "description": "Recommended SLA in hours (CRITICAL: 1, HIGH: 4, MEDIUM: 24, LOW: 72).",
                },
            },
            "required": ["priority", "justification", "sla_hours"],
        },
    },
    {
        "type": "function",
        "name": "suggest_routing",
        "description": "Recommend which team should handle this ticket.",
        "parameters": {
            "type": "object",
            "properties": {
                "team": {
                    "type": "string",
                    "enum": TEAMS,
                    "description": "The team best equipped to resolve this issue.",
                },
                "notes": {
                    "type": "string",
                    "description": "Any context the receiving team needs to know.",
                },
                "cc_teams": {
                    "type": "array",
                    "items": {"type": "string", "enum": TEAMS},
                    "description": "Additional teams that should be informed (optional).",
                },
            },
            "required": ["team", "notes"],
        },
    },
    {
        "type": "function",
        "name": "draft_response",
        "description": "Write the initial response to send to the customer.",
        "parameters": {
            "type": "object",
            "properties": {
                "subject": {
                    "type": "string",
                    "description": "Email subject line for the response.",
                },
                "body": {
                    "type": "string",
                    "description": "Full response body. Be empathetic, clear, and professional. Acknowledge the issue, set expectations, and provide next steps.",
                },
            },
            "required": ["subject", "body"],
        },
    },
    {
        "type": "function",
        "name": "finalize_triage",
        "description": "Submit the completed triage. Call this last, after all other tools have been called.",
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "One-paragraph executive summary of the ticket and recommended action.",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "3-5 searchable tags for this ticket (e.g. 'login', 'mobile', 'stripe', 'api-error').",
                },
                "internal_notes": {
                    "type": "string",
                    "description": "Any internal notes for the handling team — debugging hints, related tickets, customer history context.",
                },
            },
            "required": ["summary", "tags"],
        },
    },
]


class TriageState:
    def __init__(self):
        self.category = None
        self.category_reasoning = None
        self.priority = None
        self.sla_hours = None
        self.priority_justification = None
        self.team = None
        self.routing_notes = None
        self.cc_teams = []
        self.response_subject = None
        self.response_body = None
        self.summary = None
        self.tags = []
        self.internal_notes = None
        self.finalized = False

    def handle_tool_call(self, name: str, args: dict) -> str:
        if name == "categorize_ticket":
            self.category = args["category"]
            self.category_reasoning = args["reasoning"]
            return f"Category set to '{self.category}'."

        elif name == "set_priority":
            self.priority = args["priority"]
            self.priority_justification = args["justification"]
            self.sla_hours = args["sla_hours"]
            return f"Priority set to {self.priority} (SLA: {self.sla_hours}h)."

        elif name == "suggest_routing":
            self.team = args["team"]
            self.routing_notes = args["notes"]
            self.cc_teams = args.get("cc_teams", [])
            return f"Ticket routed to '{self.team}'."

        elif name == "draft_response":
            self.response_subject = args["subject"]
            self.response_body = args["body"]
            return "Customer response drafted."

        elif name == "finalize_triage":
            self.summary = args["summary"]
            self.tags = args.get("tags", [])
            self.internal_notes = args.get("internal_notes", "")
            self.finalized = True
            return "Triage finalized."

        return f"Unknown tool: {name}"
