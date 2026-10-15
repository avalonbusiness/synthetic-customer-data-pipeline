from pathlib import Path

from src.pipeline import normalize_record, run_pipeline, validate_record


def test_email_normalization_fixes_case_and_whitespace():
    record = normalize_record({
        "record_id": "1",
        "full_name": " Jane Doe ",
        "email": " JANE@EXAMPLE.COM ",
        "phone": " 555 0100 ",
        "source": " WEB_FORM ",
    })
    assert record["email"] == "jane@example.com"
    assert record["full_name"] == "Jane Doe"
    assert record["phone"] == "5550100"
    assert validate_record(record) == []


def test_invalid_email_is_flagged():
    record = normalize_record({
        "record_id": "2",
        "full_name": "Alex Doe",
        "email": "not-an-email",
        "phone": "",
        "source": "web_form",
    })
    assert "invalid_email" in validate_record(record)


def test_pipeline_writes_consistent_counts(tmp_path: Path):
    report = run_pipeline(rows=500, seed=42, output_dir=tmp_path)
    assert report["input_records"] == 500
    assert report["clean_output_records"] + report["duplicate_records_removed"] + report["rejected_records"] == 500
    assert (tmp_path / "clean_customers.jsonl").exists()
    assert (tmp_path / "clean_customers.parquet").exists()
    assert (tmp_path / "quality_report.json").exists()
