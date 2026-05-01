# Workspace

## Overview

pnpm workspace monorepo using TypeScript. Each package manages its own dependencies.

## Stack

- **Monorepo tool**: pnpm workspaces
- **Node.js version**: 24
- **Package manager**: pnpm
- **TypeScript version**: 5.9
- **API framework**: Express 5
- **Database**: PostgreSQL + Drizzle ORM
- **Validation**: Zod (`zod/v4`), `drizzle-zod`
- **API codegen**: Orval (from OpenAPI spec)
- **Build**: esbuild (CJS bundle)

## Key Commands

- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
- `pnpm --filter @workspace/api-server run dev` — run API server locally

See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details.

---

## HackerRank Orchestrate — Support Triage Agent

Python terminal agent for the HackerRank Orchestrate hackathon (May 2026).

### Stack
- **Language**: Python 3.11
- **LLM**: Anthropic Claude via Replit AI Integration (`claude-sonnet-4-5`)
- **Retrieval**: TF-IDF (stdlib only)
- **Web scraper**: requests + BeautifulSoup4

### Layout
```
code/               Python agent source
  main.py           CLI entry point
  agent.py          Anthropic triage + injection detection
  retriever.py      TF-IDF retriever
  corpus_fetcher.py Web scraper for 3 support sites
data/               Scraped support corpus (gitignored)
  hackerrank/
  claude/
  visa/
support_tickets/    Input/output CSVs
requirements.txt    Python dependencies
```

### Run
```bash
python code/main.py --build-corpus   # First run: scrape corpus + triage all tickets
python code/main.py                  # Subsequent runs (corpus cached)
python code/main.py --sample         # Test on sample tickets
python code/main.py --verbose        # Verbose output
```

### Support Triage Agent (from earlier session)
The `support-triage-agent/` directory is a separate interactive Rich-based triage tool for ad-hoc ticket input.
