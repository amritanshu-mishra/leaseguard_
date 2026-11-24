"""Groq adapter tests using a fake OpenAI-compatible client (no live key)."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from app.infra.llm_base import ExtractionError
from app.infra.llm_groq import GroqExtractionClient


class FakeCompletions:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=reply))])


def fake_client(replies):
    completions = FakeCompletions(replies)
    return SimpleNamespace(chat=SimpleNamespace(completions=completions)), completions


def test_valid_json_first_try_uses_temperature_zero_and_page_markers():
    payload = json.dumps(
        {"terms": [{"term_type": "base_rent_paise", "value": 4000000, "source_quote": "rent Rs. 40,000", "page": 2}]}
    )
    fake, calls = fake_client([payload])
    result = GroqExtractionClient("key", "model", "object", client=fake).extract_terms(
        "lease", ["page one", "page two"]
    )
    assert result.terms[0].value == 4_000_000
    assert calls.calls[0]["temperature"] == 0
    assert "[PAGE 2]" in calls.calls[0]["messages"][1]["content"]
    assert calls.calls[0]["response_format"] == {"type": "json_object"}


def test_schema_mode_sends_json_schema():
    fake, calls = fake_client([json.dumps({"terms": []})])
    GroqExtractionClient("key", "model", "schema", client=fake).extract_terms("lease", ["text"])
    assert calls.calls[0]["response_format"]["type"] == "json_schema"


def test_one_retry_with_validation_error_feedback():
    bad = json.dumps({"terms": [{"term_type": "base_rent_paise", "value": -1, "source_quote": "rent", "page": 1}]})
    good = json.dumps({"terms": []})
    fake, calls = fake_client([bad, good])
    GroqExtractionClient("key", "model", "object", client=fake).extract_terms("lease", ["text"])
    assert len(calls.calls) == 2
    assert "Fix these problems" in calls.calls[1]["messages"][-1]["content"]


def test_two_bad_replies_raise_extraction_error():
    bad = '{"terms": [{"unexpected": true}]}'
    fake, _ = fake_client([bad, bad])
    with pytest.raises(ExtractionError) as exc:
        GroqExtractionClient("key", "model", "object", client=fake).extract_terms("lease", ["text"])
    assert exc.value.code == "extraction_failed"


def test_provider_errors_are_wrapped():
    fake, _ = fake_client([RuntimeError("rate limited")])
    with pytest.raises(ExtractionError) as exc:
        GroqExtractionClient("key", "model", "object", client=fake).extract_terms("lease", ["text"])
    assert exc.value.code == "provider_error"


def test_missing_key_or_model_is_rejected():
    with pytest.raises(ValueError):
        GroqExtractionClient("", "model", "object", client=object())
    with pytest.raises(ValueError):
        GroqExtractionClient("key", "", "object", client=object())
