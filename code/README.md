# Support Triage Agent — Code

Python terminal agent for the HackerRank Orchestrate hackathon. Triages support tickets across HackerRank, Claude, and Visa ecosystems using RAG over a local support corpus and the Anthropic Claude API.

---

## Architecture

```
code/
├── main.py          — CLI entry point; orchestrates the full pipeline
├── agent.py         — Anthropic API calls; prompt injection & risk detection
├── retriever.py     — TF-IDF retrieval (stdlib only, no sklearn)
└── corpus_fetcher.py — Web scraper for three support sites
```

### Pipeline

```
support_tickets.csv
      │
      ▼
[corpus_fetcher]  ← scrapes HackerRank / Claude / Visa support pages
      │ data/{hackerrank,claude,visa}/*.json
      ▼
[retriever]       ← TF-IDF index; retrieves top-4 relevant docs per ticket
      │ context string
      ▼
[agent]           ← pre-checks (injection, high-risk), then calls Claude API
      │ structured JSON
      ▼
support_tickets/output.csv
```

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set your API key

Copy `.env.example` to `.env` and fill in your Anthropic key:

```bash
cp .env.example .env
# Edit .env: set ANTHROPIC_API_KEY=sk-ant-...
```

If using Replit AI Integrations, `AI_INTEGRATIONS_ANTHROPIC_BASE_URL` and
`AI_INTEGRATIONS_ANTHROPIC_API_KEY` are automatically set — no `.env` needed.

---

## Running

Always run from the **repo root**:

```bash
# First run — scrape corpus and process all tickets
python code/main.py --build-corpus

# Subsequent runs — corpus already cached
python code/main.py

# Test on sample tickets
python code/main.py --sample

# Verbose output (shows justification per ticket)
python code/main.py --verbose
```

---

## Design Decisions

### RAG with TF-IDF

Used stdlib-only TF-IDF (no sklearn) for reproducibility and zero extra
dependencies. The retriever prioritizes documents from the matching company
before expanding to the full corpus.

### Prompt injection detection

Regex pre-check before any API call. Detected injections return `escalated`
with `request_type=invalid` without touching the LLM.

### High-risk keyword detection

Tickets containing fraud/security/emergency signals trigger an extra note in
the LLM prompt to lean toward escalation, reducing hallucinated safe replies.

### Determinism

`temperature=0` throughout. The corpus scraper saves deterministic JSON files.
Re-running on the same corpus produces the same output.

### Safety-first defaults

JSON parse errors and API failures default to `status=escalated` — the safe
fallback for any unexpected situation.

---

## Output Schema

`support_tickets/output.csv` columns:

| Column | Values |
|---|---|
| `status` | `replied` \| `escalated` |
| `product_area` | e.g. `account_access`, `billing`, `fraud`, `assessment`, `security` |
| `response` | User-facing answer grounded in corpus |
| `justification` | 1-2 sentence explanation |
| `request_type` | `product_issue` \| `feature_request` \| `bug` \| `invalid` |
