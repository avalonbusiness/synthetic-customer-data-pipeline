from __future__ import annotations

import argparse
import json
import random
import re
from pathlib import Path
from typing import Any

import pandas as pd

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def generate_records(rows: int, seed: int = 42) -> list[dict[str, Any]]:
    """Generate deterministic, fictional customer records; never uses real personal data."""
    rng = random.Random(seed)
    first_names = ["Avery", "Jordan", "Taylor", "Morgan", "Riley", "Casey", "Jamie", "Quinn"]
    last_names = ["Morgan", "Patel", "Reed", "Kim", "Lopez", "Chen", "Singh", "Brown"]
    domains = ["example.com", "sample.org", "demo.net"]
    records = []

    for i in range(rows):
        first = rng.choice(first_names)
        last = rng.choice(last_names)
        email = f"{first}.{last}.{i}@{rng.choice(domains)}"
        record = {
            "record_id": f"rec_{i:07d}",
            "full_name": f"  {first} {last}  ",
            "email": f" {email.upper() if i % 11 == 0 else email} ",
            "phone": f"+1-555-{rng.randint(100, 999)}-{rng.randint(1000, 9999)}",
            "source": rng.choice(["web_form", "event", "referral"]),
        }

        # Inject deterministic data-quality issues for the demo.
        if i > 0 and i % 97 == 0:
            record["email"] = records[i - 1]["email"]  # duplicate
        if i > 0 and i % 211 == 0:
            record["email"] = "not-an-email"  # invalid
        if i > 0 and i % 307 == 0:
            record["full_name"] = "   "  # missing required value
        records.append(record)

    return records


def normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    result = dict(record)
    result["full_name"] = str(result.get("full_name", "")).strip()
    result["email"] = str(result.get("email", "")).strip().lower()
    result["phone"] = re.sub(r"\s+", "", str(result.get("phone", "")).strip())
    result["source"] = str(result.get("source", "")).strip().lower()
    return result


def validate_record(record: dict[str, Any]) -> list[str]:
    errors = []
    if not record.get("record_id", "").strip():
        errors.append("missing_record_id")
    if not record.get("full_name", "").strip():
        errors.append("missing_full_name")
    email = record.get("email", "")
    if not email:
        errors.append("missing_email")
    elif not EMAIL_RE.match(email):
        errors.append("invalid_email")
    if not record.get("source", "").strip():
        errors.append("missing_source")
    return errors


def run_pipeline(rows: int, seed: int, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    raw = generate_records(rows=rows, seed=seed)

    with (output_dir / "raw_customers.jsonl").open("w", encoding="utf-8") as f:
        for record in raw:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    valid = []
    rejected = []
    for raw_record in raw:
        normalized = normalize_record(raw_record)
        errors = validate_record(normalized)
        if errors:
            rejected.append({**normalized, "validation_errors": errors})
        else:
            valid.append(normalized)

    # Deterministic keep-first deduplication by normalized email.
    seen_emails = set()
    unique = []
    duplicate_count = 0
    for record in valid:
        key = record["email"]
        if key in seen_emails:
            duplicate_count += 1
            continue
        seen_emails.add(key)
        unique.append(record)

    def write_jsonl(path: Path, items: list[dict[str, Any]]) -> None:
        with path.open("w", encoding="utf-8") as f:
            for item in items:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

    write_jsonl(output_dir / "clean_customers.jsonl", unique)
    write_jsonl(output_dir / "rejected_customers.jsonl", rejected)
    pd.DataFrame(unique).to_parquet(output_dir / "clean_customers.parquet", index=False)

    report = {
        "pipeline_version": "1.0.0",
        "seed": seed,
        "input_records": len(raw),
        "rejected_records": len(rejected),
        "valid_records_before_deduplication": len(valid),
        "duplicate_records_removed": duplicate_count,
        "clean_output_records": len(unique),
        "deduplication_key": "normalized_email",
        "validation_rules": [
            "record_id required",
            "full_name required",
            "email required and must match basic email pattern",
            "source required",
        ],
    }
    (output_dir / "quality_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Synthetic customer data pipeline")
    parser.add_argument("--rows", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    args = parser.parse_args()
    if args.rows < 1:
        parser.error("--rows must be >= 1")
    report = run_pipeline(args.rows, args.seed, args.output_dir)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
