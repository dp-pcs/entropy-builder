"""
CLI runner for manual end-to-end testing of the pipeline.
Usage: python -m pipeline.run --config config.json --output vault.zip

config.json format:
{
  "user_name": "Test User",
  "user_role": "ic",
  "account_manager_name": "Test User",
  "team_members": [],
  "notion_token": "ntn_...",
  "notion_database_id": "28485e927d3181c89d6cdd6fd57ea07d",
  "google_credentials": {},
  "readai_access_token": "...",
  "fireworks_api_key": "...",
  "interview_answers": {"role": "Account Manager", "books": ["Atomic Habits"]},
  "entropy_template_path": "/Users/davidproctor/Documents/GitHub/entropy"
}
"""
import argparse
import json
import sys
from pathlib import Path
from .models import JobConfig
from .ingest import ingest
from .kimi import generate_wiki, analyze_gaps
from .notion_pull import pull_customers, build_intelligence_summary, build_customer_domains, build_hub_nodes
from .vault_builder import build_vault


def main():
    parser = argparse.ArgumentParser(description="Run Entropy pipeline")
    parser.add_argument("--config", required=True, help="Path to config JSON")
    parser.add_argument("--output", default="vault.zip", help="Output ZIP path")
    parser.add_argument("--files", nargs="*", help="Files to ingest (paths)")
    parser.add_argument(
        "--debug-dir",
        help="Dump per-chunk raw responses + parse diagnostics here for offline replay",
    )
    args = parser.parse_args()

    import logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    cfg_data = json.loads(Path(args.config).read_text())
    cfg = JobConfig(**cfg_data)

    print("Step 1: Ingesting files...")
    sources = []
    for fpath in (args.files or []):
        p = Path(fpath)
        ext = p.suffix.lower()
        ftype = "zip" if ext == ".zip" else ("opml" if ext == ".opml" else "file")
        sources.append({"type": ftype, "content": p.read_bytes(), "filename": p.name})
    ingested = ingest(sources)
    print(f"  Ingested {len(ingested)} files")

    print("Step 2: Generating wiki (Kimi Pass 1)...")
    wiki_files = generate_wiki(cfg, ingested, debug_dir=args.debug_dir)
    print(f"  Generated {len(wiki_files)} wiki files")

    print("Step 3: Analyzing gaps (Kimi Pass 2)...")
    gaps = analyze_gaps(cfg, wiki_files)
    print(f"  Found {len(gaps)} gaps")
    for g in gaps:
        print(f"  - [{g.category}] {g.description}")

    print("Step 4: Pulling org data...")
    customers = pull_customers(cfg)
    cfg.product_lines = list({c.product for c in customers})
    customer_files = [build_intelligence_summary(c) for c in customers]
    domains_vf = build_customer_domains(customers)
    hub_nodes = build_hub_nodes(customers)
    print(f"  Pulled {len(customers)} customers across {cfg.product_lines}")

    print("Step 4b: Pulling Gmail emails...")
    from .gmail_pull import pull_emails
    email_stubs = pull_emails(cfg, json.loads(domains_vf.content))
    print(f"  Pulled {len(email_stubs)} email stubs")

    print("Step 4c: Pulling read.ai transcripts...")
    from .readai_pull import pull_transcripts
    transcript_stubs = pull_transcripts(cfg, json.loads(domains_vf.content))
    print(f"  Pulled {len(transcript_stubs)} transcript stubs")

    all_customer_files = customer_files + [domains_vf] + email_stubs + transcript_stubs

    print("Step 5: Building vault ZIP...")
    connector_stats = {"gmail": len(email_stubs), "readai": len(transcript_stubs)}
    zip_bytes = build_vault(
        cfg, wiki_files, customers, all_customer_files, hub_nodes, gaps,
        connector_stats=connector_stats,
    )
    Path(args.output).write_bytes(zip_bytes)
    print(f"  Vault written to {args.output} ({len(zip_bytes):,} bytes)")
    print("Done.")


if __name__ == "__main__":
    main()
