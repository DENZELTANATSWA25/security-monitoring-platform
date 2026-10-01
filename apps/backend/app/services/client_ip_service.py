# Trusteed client IP extraction for HTTP requests.

from ipaddress import ip_address

from fastapi import Request

from app.core.config import settings

def _normalise_ip(value: str) -> str | None:
    """Return a canonical IP address or None for an invalid value."""

    try:
        return str(ip_address(value.strip()))
    except ValueError:
        return None

def _trusted_proxy_ips() -> set[str]:
    # Return configured trusted proxy addresses in canonical form.

    trusted_ips: set[str] = set()

    for value in settings.TRUSTED_PROXY_IPS.split(","):
        value = value.strip()

        if not value:
            continue

        normalised = _normalise_ip(value)

        if normalised is not None:
            trusted_ips.add(normalised)


    return trusted_ips  

def get_client_ip(
    request: Request,
) -> str | None:
    """
    Return the trustworthy client IP address for a request.

    Forwarding headers are considered only when the immediate network peer is
    explicitly configured as a trusted proxy.

    The X-Forwarded-For chain is evaluated from right to left. Trusted proxy
    addresses are skipped until the first untrusted address is found. That
    address is treated as the originating client.
    """

    if request.client is None:
        return None

    peer_ip = _normalise_ip(request.client.host)

    if peer_ip is None:
        return None

    trusted_proxies = _trusted_proxy_ips()

    # Never trust forwarding headers from an untrusted immediate peer.
    if peer_ip not in trusted_proxies:
        return peer_ip

    forwarded_for = request.headers.get("x-forwarded-for")

    if not forwarded_for:
        return peer_ip

    forwarded_ips: list[str] = []

    for value in forwarded_for.split(","):
        normalised = _normalise_ip(value)

        # Reject the entire forwarded chain if any entry is malformed.
        if normalised is None:
            return peer_ip

        forwarded_ips.append(normalised)

    if not forwarded_ips:
        return peer_ip

    # Walk from the proxy nearest to us towards the original client.
    for forwarded_ip in reversed(forwarded_ips):
        if forwarded_ip not in trusted_proxies:
            return forwarded_ip

    # Every forwarded address was itself a trusted proxy.
    return peer_ip