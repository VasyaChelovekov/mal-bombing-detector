"""Tests for failure record helpers."""

from datetime import datetime

from src.core.models import FailureRecord, FailureStage


def test_failure_record_from_exception_preserves_schema():
    exc = ValueError("bad data")
    record = FailureRecord.from_exception(
        mal_id=42,
        stage=FailureStage.ANALYZE,
        error=exc,
        title="Sample",
        url="https://example.com",
    )

    assert record.mal_id == 42
    assert record.stage == FailureStage.ANALYZE
    assert record.error_type == "ValueError"
    assert record.message == "bad data"
    assert record.title == "Sample"
    assert record.url == "https://example.com"
    assert isinstance(record.timestamp, datetime)

    as_dict = record.to_dict()
    assert as_dict["mal_id"] == 42
    assert as_dict["stage"] == "analyze"
    assert as_dict["error_type"] == "ValueError"
    assert as_dict["message"] == "bad data"
    assert as_dict["title"] == "Sample"
    assert as_dict["url"] == "https://example.com"
    assert "timestamp" in as_dict and as_dict["timestamp"] is not None


def test_failure_record_from_message_preserves_schema():
    record = FailureRecord.from_message(
        mal_id=7,
        stage=FailureStage.FETCH,
        error_type="NoDistribution",
        message="missing distribution",
        title="Example",
        url="https://example.com/7",
    )

    assert record.mal_id == 7
    assert record.stage == FailureStage.FETCH
    assert record.error_type == "NoDistribution"
    assert record.message == "missing distribution"
    assert record.title == "Example"
    assert record.url == "https://example.com/7"
    assert isinstance(record.timestamp, datetime)

    as_dict = record.to_dict()
    assert as_dict["stage"] == "fetch"
    assert as_dict["error_type"] == "NoDistribution"
    assert as_dict["message"] == "missing distribution"
    assert "timestamp" in as_dict and as_dict["timestamp"] is not None
