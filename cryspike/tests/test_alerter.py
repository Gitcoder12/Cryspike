from unittest.mock import MagicMock

from cryspike.alerter import (
    format_discord_embed,
    format_text_message,
    send_webhook,
)


def test_discord_payload_truncates_process_field() -> None:
    processes = [
        {"pid": index, "name": "a-very-long-process-name" * 8, "used_memory_mb": 64}
        for index in range(50)
    ]
    payload = format_discord_embed(0, 99.5, processes)
    assert payload["embeds"][0]["fields"][2]["value"]
    assert len(payload["embeds"][0]["fields"][2]["value"]) <= 1000


def test_text_webhook_payload_contains_processes() -> None:
    payload = format_text_message(
        1, 91.0, [{"pid": 12, "name": "python", "used_memory_mb": 512}]
    )
    assert "GPU: 1" in payload["text"]
    assert "python" in payload["text"]


def test_http_webhook_is_rejected_before_network_call(monkeypatch) -> None:
    def unexpected_call(*args, **kwargs):
        raise AssertionError("Network should not be called for HTTP URLs.")

    monkeypatch.setattr("cryspike.alerter.urlopen", unexpected_call)
    assert send_webhook("http://example.com/hook", {"text": "test"}) is False


def test_https_webhook_posts_json(monkeypatch) -> None:
    response = MagicMock()
    response.status = 204
    calls = []

    def fake_urlopen(request, timeout):
        calls.append((request, timeout))
        return response

    monkeypatch.setattr("cryspike.alerter.urlopen", fake_urlopen)
    assert send_webhook("https://example.com/hooks/abc", {"text": "hello"}) is True
    assert calls[0][1] == 10
    assert calls[0][0].get_header("Content-type") == "application/json"
