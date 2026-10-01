"""Tests for trusted HTTP client IP extraction."""

from starlette.requests import Request

from app.core.config import settings
from app.services.client_ip_service import get_client_ip


def _request(
    *,
    client_host: str,
    forwarded_for: str | None = None,
) -> Request:
    """Build a minimal HTTP request for client-IP tests."""

    headers: list[tuple[bytes, bytes]] = []

    if forwarded_for is not None:
        headers.append(
            (
                b"x-forwarded-for",
                forwarded_for.encode(),
            )
        )

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": headers,
        "client": (client_host, 12345),
    }

    return Request(scope)


def test_direct_request_uses_peer_ip(
    monkeypatch,
) -> None:
    """Direct requests should use the immediate peer address."""

    monkeypatch.setattr(
        settings,
        "TRUSTED_PROXY_IPS",
        "",
    )

    request = _request(
        client_host="203.0.113.10",
    )

    assert get_client_ip(request) == "203.0.113.10"


def test_untrusted_peer_cannot_spoof_forwarded_ip(
    monkeypatch,
) -> None:
    """Forwarding headers from untrusted peers must be ignored."""

    monkeypatch.setattr(
        settings,
        "TRUSTED_PROXY_IPS",
        "",
    )

    request = _request(
        client_host="203.0.113.10",
        forwarded_for="8.8.8.8",
    )

    assert get_client_ip(request) == "203.0.113.10"


def test_trusted_proxy_uses_forwarded_client_ip(
    monkeypatch,
) -> None:
    """A trusted proxy may supply the original client address."""

    monkeypatch.setattr(
        settings,
        "TRUSTED_PROXY_IPS",
        "10.0.0.10",
    )

    request = _request(
        client_host="10.0.0.10",
        forwarded_for="8.8.8.8",
    )

    assert get_client_ip(request) == "8.8.8.8"


def test_invalid_forwarded_ip_falls_back_to_peer(
    monkeypatch,
) -> None:
    """Malformed forwarded addresses must not replace the peer address."""

    monkeypatch.setattr(
        settings,
        "TRUSTED_PROXY_IPS",
        "10.0.0.10",
    )

    request = _request(
        client_host="10.0.0.10",
        forwarded_for="not-an-ip",
    )

    assert get_client_ip(request) == "10.0.0.10"

def test_forwarded_chain_skips_trusted_proxies(
    monkeypatch,
) -> None:
    """Trusted proxy hops should be skipped when resolving the client."""

    monkeypatch.setattr(
        settings,
        "TRUSTED_PROXY_IPS",
        "10.0.0.10,10.0.0.20",
    )

    request = _request(
        client_host="10.0.0.10",
        forwarded_for="8.8.8.8, 10.0.0.20",
    )

    assert get_client_ip(request) == "8.8.8.8"

def test_forwarded_chain_stops_at_first_untrusted_address(
    monkeypatch,
) -> None:
    """Values before the first untrusted hop must not be blindly trusted."""

    monkeypatch.setattr(
        settings,
        "TRUSTED_PROXY_IPS",
        "10.0.0.10",
    )

    request = _request(
        client_host="10.0.0.10",
        forwarded_for="8.8.8.8, 203.0.113.50",
    )

    assert get_client_ip(request) == "203.0.113.50"