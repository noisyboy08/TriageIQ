import os

BASE_URL = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
API_KEY = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY", "placeholder")
MODEL = "gpt-5.1"

SYSTEM_PROMPT = """You are a senior support triage agent. Your job is to analyze incoming support tickets and produce a structured triage report.

For every ticket you receive, you MUST call the following tools in order:
1. categorize_ticket — assign a category
2. set_priority — assign a priority level with a justification
3. suggest_routing — recommend which team should handle it
4. draft_response — write an empathetic, helpful first response to the customer
5. finalize_triage — submit the completed triage report

Use your judgment to identify urgency signals: words like "down", "outage", "can't access", "lost data", "urgent", "critical" should trigger HIGH or CRITICAL priority. Billing or account questions are typically MEDIUM. Feature requests are LOW.

Be thorough, be empathetic, and be precise. Real customers are waiting."""

CATEGORIES = [
    "Bug / Technical Issue",
    "Billing & Payments",
    "Account & Access",
    "Feature Request",
    "Performance / Outage",
    "Integration / API",
    "Data Loss / Corruption",
    "Security",
    "General Inquiry",
    "Other",
]

PRIORITIES = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

TEAMS = [
    "Engineering — Backend",
    "Engineering — Frontend",
    "Engineering — Infrastructure / SRE",
    "Billing & Finance",
    "Account Management",
    "Security Response",
    "Product",
    "Customer Success",
    "General Support",
]
