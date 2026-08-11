from app.pii import scrub_text
from app.logging_config import scrub_event


def test_scrub_email() -> None:
    out = scrub_text("Email me at student@vinuni.edu.vn")
    assert "student@" not in out
    assert "REDACTED_EMAIL" in out


def test_scrub_common_vietnamese_phone_formats() -> None:
    phone_numbers = (
        "0901234567",
        "090 123 4567",
        "090.123.4567",
        "090-123-4567",
        "+84 90 123 4567",
    )

    for phone_number in phone_numbers:
        out = scrub_text(f"Contact: {phone_number}")
        assert phone_number not in out
        assert "REDACTED_PHONE_VN" in out


def test_logging_processor_scrubs_nested_payload_values() -> None:
    record = {
        "event": "request_failed",
        "payload": {"exception": {"detail": "Contact student@vinuni.edu.vn"}},
    }

    scrubbed = scrub_event(None, "error", record)

    assert "student@" not in str(scrubbed)
    assert "[REDACTED_EMAIL]" in str(scrubbed)
