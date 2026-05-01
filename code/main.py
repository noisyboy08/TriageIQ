#!/usr/bin/env python3
"""
main.py — CLI entry point for the support triage agent.

Usage:
  python code/main.py                  Process support_tickets.csv → write output.csv
  python code/main.py --build-corpus   Scrape corpus first, then process
  python code/main.py --sample         Run on sample_support_tickets.csv
  python code/main.py --verbose        Show per-ticket details

Run from the repo root.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

import anthropic
from agent import triage_ticket, _make_client
from corpus_fetcher import fetch_all_corpus, DATA_DIR
from retriever import TFIDFRetriever, load_corpus, get_context_for_ticket

TICKETS_DIR = ROOT / "support_tickets"
INPUT_CSV = TICKETS_DIR / "support_tickets.csv"
SAMPLE_CSV = TICKETS_DIR / "sample_support_tickets.csv"
OUTPUT_CSV = TICKETS_DIR / "output.csv"

OUTPUT_COLUMNS = [
    "Issue", "Subject", "Company",
    "status", "product_area", "response", "justification", "request_type",
]


def _corpus_is_empty() -> bool:
    for folder in (DATA_DIR / "hackerrank", DATA_DIR / "claude", DATA_DIR / "visa"):
        if folder.exists() and any(folder.glob("*.json")):
            return False
    return True


def _read_tickets(csv_path: Path) -> list[dict]:
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def _write_output(rows: list[dict], path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _append_log(entry: str) -> None:
    import datetime
    log_dir = Path.home() / "hackerrank_orchestrate"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "log.txt"
    timestamp = datetime.datetime.now().astimezone().isoformat()
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"\n## [{timestamp}] {entry}\n")


def run(input_csv: Path, verbose: bool = False) -> None:
    print(f"\n[main] Loading corpus from {DATA_DIR}…")
    corpus = load_corpus()
    if not corpus:
        print("[main] WARNING: Corpus is empty. Run with --build-corpus first.")

    print(f"[main] Building TF-IDF index over {len(corpus)} documents…")
    retriever = TFIDFRetriever()
    retriever.build(corpus)

    print(f"[main] Reading tickets from {input_csv}…")
    tickets = _read_tickets(input_csv)
    total = len(tickets)
    print(f"[main] {total} tickets to process\n")

    client = _make_client()
    results: list[dict] = []
    replied_count = 0
    escalated_count = 0

    for i, row in enumerate(tickets, 1):
        issue = row.get("Issue", "").strip()
        subject = row.get("Subject", "").strip()
        company = row.get("Company", "").strip() or None

        context = get_context_for_ticket(issue, subject, company, retriever)

        result = triage_ticket(issue, subject, company, context, client)

        status = result.get("status", "escalated")
        product_area = result.get("product_area", "general_support")
        request_type = result.get("request_type", "product_issue")

        if status == "replied":
            replied_count += 1
        else:
            escalated_count += 1

        label = f"[{i}/{total}]"
        print(f"{label} Company: {company or 'None':<14} | Status: {status:<10} | Type: {request_type}")
        if verbose:
            print(f"         Product area: {product_area}")
            print(f"         Justification: {result.get('justification', '')}")
            print()

        out_row = {
            "Issue": issue,
            "Subject": subject,
            "Company": company or "",
            "status": status,
            "product_area": product_area,
            "response": result.get("response", ""),
            "justification": result.get("justification", ""),
            "request_type": request_type,
        }
        results.append(out_row)

    print(f"\n[main] Writing output to {OUTPUT_CSV}…")
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    _write_output(results, OUTPUT_CSV)

    print(f"\n{'=' * 50}")
    print(f"  Total tickets  : {total}")
    print(f"  Replied        : {replied_count}")
    print(f"  Escalated      : {escalated_count}")
    print(f"  Output written : {OUTPUT_CSV}")
    print(f"{'=' * 50}\n")

    _append_log(
        f"Triage run complete — {total} tickets, {replied_count} replied, {escalated_count} escalated\n"
        f"Input: {input_csv}\nOutput: {OUTPUT_CSV}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Support Triage Agent — HackerRank Orchestrate"
    )
    parser.add_argument(
        "--build-corpus",
        action="store_true",
        help="Scrape the support corpus before running triage",
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Run on sample_support_tickets.csv instead of support_tickets.csv",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed output per ticket",
    )
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("AI_INTEGRATIONS_ANTHROPIC_API_KEY")
    if not api_key:
        print(
            "ERROR: No Anthropic API key found.\n"
            "  Option A: Set ANTHROPIC_API_KEY in your .env file\n"
            "  Option B: Use Replit AI Integrations (AI_INTEGRATIONS_ANTHROPIC_API_KEY is auto-set)\n"
        )
        sys.exit(1)

    if args.build_corpus or _corpus_is_empty():
        print("[main] Corpus is missing or --build-corpus specified. Fetching now…")
        fetch_all_corpus()

    input_csv = SAMPLE_CSV if args.sample else INPUT_CSV
    if not input_csv.exists():
        print(f"ERROR: Input file not found: {input_csv}")
        sys.exit(1)

    run(input_csv, verbose=args.verbose)


if __name__ == "__main__":
    main()
