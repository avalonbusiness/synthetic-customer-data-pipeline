# Synthetic Customer Data Pipeline

A small, reproducible portfolio project demonstrating synthetic data generation, normalization,
deduplication, schema validation, quality reporting, and JSONL/Parquet exports.

> This is a demonstration project using entirely synthetic records. It is not evidence of prior
> client work. Run it and report the actual metrics produced by your run.

## Features
- Generate deterministic synthetic customer records from a fixed random seed
- Normalize names, email addresses, and phone strings
- Validate required fields and email shape
- Detect duplicates using normalized email as a stable key
- Export raw and cleaned JSONL, cleaned Parquet, rejected records, and a JSON quality report
- Unit tests and GitHub Actions CI

## Requirements
- Python 3.10+
- See `requirements.txt`

## Run locally
```bash
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
python -m src.pipeline --rows 10000 --seed 42 --output-dir outputs
pytest -q
```

The pipeline prints a summary and writes files into `outputs/`:
- `raw_customers.jsonl`
- `clean_customers.jsonl`
- `clean_customers.parquet`
- `rejected_customers.jsonl`
- `quality_report.json`

Do not commit generated output files unless you intentionally want to publish a sample. The `.gitignore`
excludes `outputs/` by default.

## Pipeline design
1. Generate deterministic synthetic records.
2. Normalize whitespace and case in identity fields.
3. Validate required fields and email format.
4. Reject invalid records with reasons rather than silently dropping them.
5. Deduplicate valid records by normalized email, keeping the first record.
6. Export results and record counts in a quality report.

## Example failure mode and fix
A common issue in customer-data pipelines is failing to deduplicate `JANE@example.com` and
` jane@example.com ` because raw strings differ. This pipeline normalizes email values with
whitespace trimming and lowercasing before deduplication. The test suite includes a regression
test for this behavior.

## Reproducibility and provenance
- The synthetic generator accepts a fixed seed.
- No real personal data is used.
- The report records input, valid, rejected, duplicate, and output counts.
- The project uses a pinned dependency file; update it intentionally and rerun tests before release.

## Limitations
This is my compact portfolio, not a production PII resolution system.
Production systems should define business-specific matching rules, preserve source IDs, and review
ambiguous matches.
