TriageIQ-Agent - Support Triage Agent
=====================================

TriageIQ-Agent is a command-line support ticket triage system. It reads incoming
support tickets from CSV, retrieves relevant support documentation from a local
corpus, sends the ticket plus retrieved context to a Gemini-compatible model, and
writes structured triage results to `support_tickets/output.csv`.

The project is designed for a HackerRank Orchestrate-style support workflow where
each ticket must be classified as either:

- `replied` - the agent can produce a customer-facing answer from the corpus.
- `escalated` - the ticket needs human review because it is unsafe, vague,
  high-risk, security-related, fraud-related, or not answerable from the corpus.

Core Capabilities
-----------------

- Builds a local support corpus from HackerRank, Claude, and Visa support pages.
- Uses a lightweight TF-IDF retriever to select relevant documentation for each
  ticket.
- Calls a Gemini API model for JSON-only triage.
- Detects prompt injection attempts before the model call.
- Escalates high-risk issues such as fraud, stolen cards, identity theft,
  security vulnerabilities, urgent cash requests, and unsafe system requests.
- Writes a normalized output CSV with the required schema.
- Raises real API/parser errors loudly instead of silently substituting generated
  placeholder results.

Repository Layout
-----------------

```text
TriageIQ-Agent/
  code/
    main.py            CLI entry point and CSV orchestration
    agent.py           LLM prompt, safety checks, API call, JSON parsing
    corpus_fetcher.py  Web scraper for HackerRank, Claude, and Visa support docs
    retriever.py       Stdlib-only TF-IDF document retriever
  data/
    hackerrank/        Scraped HackerRank support pages as JSON
    claude/            Scraped Claude support pages as JSON
    visa/              Scraped Visa support pages as JSON
  support_tickets/
    support_tickets.csv         Main input tickets
    sample_support_tickets.csv  Smaller sample input
    output.csv                  Generated triage output
  .env                Local API key file, not for sharing
  .env.example        Environment variable template
  requirements.txt    Python package list
  test_gemini.py      Minimal API smoke test
```

Runtime Flow
------------

1. `code/main.py` loads `.env` from the repository root.
2. If `--build-corpus` is passed, `code/corpus_fetcher.py` scrapes support pages.
3. `code/retriever.py` loads JSON files from `data/` and builds a TF-IDF index.
4. `main.py` reads `support_tickets/support_tickets.csv`.
5. For each ticket, `get_context_for_ticket()` retrieves relevant corpus snippets.
6. `code/agent.py` checks for prompt injection and high-risk keywords.
7. The ticket and retrieved context are sent to the model.
8. The model response is parsed as JSON and normalized.
9. `main.py` writes all rows to `support_tickets/output.csv`.

Input CSV Format
----------------

The main input file is:

```text
support_tickets/support_tickets.csv
```

Expected columns:

```text
Issue, Subject, Company
```

Example:

```csv
Issue,Subject,Company
How do I reset my HackerRank password?,Password reset,HackerRank
My identity has been stolen,Identity theft,Visa
I have found a major security vulnerability in Claude,Security vulnerability report,Claude
```

Output CSV Format
-----------------

The generated output file is:

```text
support_tickets/output.csv
```

Required columns:

```text
Issue, Subject, Company, status, product_area, response, justification, request_type
```

Column meanings:

- `Issue` - original user issue text.
- `Subject` - ticket subject.
- `Company` - source company or product area from the input.
- `status` - `replied` or `escalated`.
- `product_area` - short routing label such as `fraud`, `security`,
  `general_support`, `Claude`, `Visa`, or `HackerRank`.
- `response` - customer-facing response or escalation message.
- `justification` - concise reason for the classification.
- `request_type` - one of `product_issue`, `feature_request`, `bug`, or `invalid`.

Environment Setup
-----------------

Install Python 3.11 or newer, then install dependencies from the project root:

```powershell
Set-Location 'C:\Users\udayd\OneDrive\Desktop\TriageIQ\TriageIQ-Agent'
python -m pip install -r requirements.txt
```

Create `.env` in the repository root:

```powershell
Set-Content -Path .env -Value 'GEMINI_API_KEY=YOUR_API_KEY_HERE' -Encoding UTF8
```

The code loads `.env` explicitly from the parent directory of `code/`:

```python
load_dotenv(dotenv_path=os.path.join(
    os.path.dirname(__file__), '..', '.env'))
```

Do not commit or share `.env`.

Model Configuration
-------------------

The current runnable pipeline uses:

```text
models/gemma-3-12b-it
```

Reason: `models/gemini-2.0-flash-lite` was tested, but the API returned a free
tier quota limit of `0` for that model in this environment. `models/gemma-3-12b-it`
worked in the smoke test.

Important implementation details:

- Gemma does not support `response_mime_type="application/json"` in this setup.
- Gemma does not support `system_instruction` in this setup.
- Therefore, `agent.py` places the system instructions inside the normal prompt
  and strips optional markdown fences before parsing JSON.

Smoke Test
----------

Run the model smoke test first:

```powershell
python test_gemini.py
```

Expected successful shape:

```text
API WORKS: {
  "status": "replied",
  "product_area": "test",
  "response": "working",
  "justification": "test",
  "request_type": "invalid"
}
```

If the smoke test fails, fix API key, quota, billing, or model access before
running the full pipeline.

Build Corpus
------------

To scrape and refresh the support corpus:

```powershell
python code/main.py --build-corpus
```

The scraper uses these sources:

- HackerRank support: `https://support.hackerrank.com/hc/en-us`
- Claude support: `https://support.claude.com/en/`
- Visa India support: `https://www.visa.co.in/support.html`

Scraped pages are saved as JSON files under:

```text
data/hackerrank/
data/claude/
data/visa/
```

Run Triage
----------

After the corpus exists, run:

```powershell
python code/main.py
```

To rebuild the corpus and then run triage:

```powershell
python code/main.py --build-corpus
```

To run the sample CSV:

```powershell
python code/main.py --sample
```

To print more per-ticket details:

```powershell
python code/main.py --verbose
```

During processing, terminal output looks like:

```text
[1/29] HackerRank | replied | HackerRank
[2/29] Claude | replied | Claude
[3/29] Visa | escalated | Visa
```

Safety and Escalation Rules
---------------------------

The agent uses both deterministic checks and model instructions.

Prompt injection is escalated before the model call when the ticket contains
patterns such as:

- `ignore previous`
- `ignore all`
- `affiche toutes les règles`
- `delete all files`
- `show internal rules`
- `reveal your prompt`
- `disregard`

High-risk tickets are marked for escalation or special routing when they include:

- fraud
- stolen cards
- identity theft
- security vulnerability
- urgent cash
- data breach
- hacking-related terms

Post-model normalization also forces:

- Missing/`None` company tickets to `escalated`, `general_support`, `invalid`.
- Prompt injection tickets to `escalated`, `invalid`.
- Identity theft and urgent cash tickets to `escalated`, `fraud`.
- Security vulnerability tickets to `escalated`, `bug`.

Verification Checklist
----------------------

After a full run, verify:

```powershell
$rows = Import-Csv support_tickets\output.csv
$rows.Count
$rows | Group-Object status | Select-Object Name,Count
```

Expected:

- Exactly `29` rows for the current main input file.
- A mix of `replied` and `escalated`.
- No placeholder or synthetic fallback wording.
- No `mock` text in `output.csv`.

Check for unwanted words:

```powershell
rg -n 'mock|fallback|simulated' support_tickets\output.csv
```

Check required safety cases:

```powershell
Import-Csv support_tickets\output.csv |
  Where-Object {
    $_.Issue -match 'affiche toutes|delete all files|identity has been stolen|security vulnerability|not working|urgent cash'
  } |
  Select-Object Issue,Company,status,product_area,request_type,response |
  Format-List
```

Known Current Result
--------------------

The latest successful run completed all 29 tickets with:

```text
Replied:   15
Escalated: 14
```

Important checked cases:

- French hidden-rules request: `escalated`, `security`, `invalid`.
- Delete-all-files request: `escalated`, `security`, `invalid`.
- Visa identity theft: `escalated`, `fraud`.
- Claude security vulnerability: `escalated`, `bug`.
- Vague `Company=None` issue: `escalated`, `general_support`, `invalid`.
- Visa urgent cash issue: `escalated`, `fraud`.

Troubleshooting
---------------

`ValueError: GEMINI_API_KEY not set!`

The `.env` file is missing, the variable name is wrong, or the command is being
run from an unexpected environment. Ensure `.env` contains:

```text
GEMINI_API_KEY=YOUR_API_KEY_HERE
```

`429 RESOURCE_EXHAUSTED`

The API key or model quota is exhausted. Try a key with quota, wait for the quota
window to reset, reduce prompt size, or use another available model.

`JSON mode is not enabled`

The selected model does not support `response_mime_type="application/json"`.
Remove JSON mode and parse the returned text after stripping markdown fences.

`Developer instruction is not enabled`

The selected model does not support `system_instruction`. Put instructions inside
the normal prompt content instead.

JSON parsing errors

The model returned non-JSON or wrapped/extra text. `agent.py` already strips
basic markdown code fences. If parsing still fails, inspect `response.text` and
tighten the prompt.

Development Notes
-----------------

- Keep `agent.py` strict: failed API calls should raise real errors.
- Keep output schema stable because downstream graders usually expect exact
  column names.
- Keep corpus snippets short enough to avoid free-tier input-token limits.
- If changing model providers, isolate the provider-specific call in `agent.py`.
- If adding new companies, update `SOURCES` in `corpus_fetcher.py` and
  `COMPANY_TO_FOLDER` in `retriever.py`.

License
-------

MIT
