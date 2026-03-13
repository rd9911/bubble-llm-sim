from bubble_sim.utils.redaction import redact_secrets, redact_trace_row


def test_redact_api_key():
    text = "key=sk-abcdefghijklmnopqrstuvwxyz1234567890"
    result = redact_secrets(text)
    assert "sk-" not in result
    assert "[REDACTED]" in result


def test_redact_email():
    text = "contact user@example.com for info"
    result = redact_secrets(text)
    assert "user@example.com" not in result


def test_redact_bearer():
    text = "Authorization: Bearer abc123def456xyz.secret.token"
    result = redact_secrets(text)
    assert "abc123def456xyz" not in result


def test_redact_trace_row():
    row = {
        "api_key": "sk-abcdefghijklmnopqrstuvwxyz1234567890",
        "action": "buy",
        "price": 100,
    }
    clean = redact_trace_row(row)
    assert "sk-" not in clean["api_key"]
    assert clean["action"] == "buy"
    assert clean["price"] == 100
