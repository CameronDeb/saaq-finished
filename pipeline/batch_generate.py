#!/usr/bin/env python3
"""
Batch generate SAAQ reports for all pilot respondents.

Usage:
    python batch_generate.py --data pilot_data.json --output ./output
    python batch_generate.py --data pilot_data.json --output ./output --dry-run
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

# Add parent dir to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")


def analyze_one(subject: str, responses: dict) -> dict:
    """Analyze one respondent via Claude API."""
    from services.analyzer import analyze_responses_sync
    return analyze_responses_sync(subject, responses)


def build_docx(report_data: dict, output_path: str):
    """Build DOCX from report JSON."""
    pipeline_dir = Path(__file__).parent
    json_path = pipeline_dir / "src" / "_temp_batch.json"

    with open(json_path, "w") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)

    result = subprocess.run(
        ["node", str(pipeline_dir / "build_report.js"), str(json_path), output_path],
        capture_output=True, text=True, timeout=30,
    )
    json_path.unlink(missing_ok=True)

    if result.returncode != 0:
        raise Exception(f"DOCX build failed: {result.stderr}")


def main():
    parser = argparse.ArgumentParser(description="Batch generate SAAQ reports")
    parser.add_argument("--data", required=True, help="JSON file with respondent data")
    parser.add_argument("--output", default="./output", help="Output directory")
    parser.add_argument("--dry-run", action="store_true", help="Just show what would be generated")
    parser.add_argument("--json-only", action="store_true", help="Generate JSON analysis only (no DOCX)")
    args = parser.parse_args()

    with open(args.data) as f:
        respondents = json.load(f)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"{'='*60}")
    print(f"SAAQ Batch Report Generator")
    print(f"{'='*60}")
    print(f"Respondents: {len(respondents)}")
    print(f"Output: {output_dir}")
    print()

    if args.dry_run:
        for r in respondents:
            name = r.get("first_name", r.get("name", "Unknown"))
            n_responses = len(r.get("responses", {}))
            print(f"  Would generate: SAAQReport-{name}.docx ({n_responses} responses)")
        print(f"\nTotal: {len(respondents)} reports")
        return

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set. Add it to .env")
        sys.exit(1)

    succeeded = 0
    failed = 0

    for i, respondent in enumerate(respondents, 1):
        name = respondent.get("first_name", respondent.get("name", "Unknown"))
        responses = respondent.get("responses", {})
        print(f"[{i}/{len(respondents)}] Generating report for {name}...")

        try:
            # Analyze
            print(f"  Analyzing ({len(responses)} responses)...")
            report_data = analyze_one(name, responses)

            # Save JSON
            json_path = output_dir / f"SAAQReport-{name}.json"
            with open(json_path, "w") as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            print(f"  ✅ JSON saved: {json_path}")

            if not args.json_only:
                # Build DOCX
                docx_path = str(output_dir / f"SAAQReport-{name}.docx")
                build_docx(report_data, docx_path)
                print(f"  ✅ DOCX saved: {docx_path}")

            succeeded += 1

            # Brief pause to avoid rate limiting
            if i < len(respondents):
                time.sleep(2)

        except Exception as e:
            print(f"  ❌ FAILED: {e}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"Batch complete: {succeeded} succeeded, {failed} failed")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
