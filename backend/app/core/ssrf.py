import asyncio
import ipaddress
import socket
from urllib.parse import urlparse
from typing import Set
from fastapi import HTTPException, status

# Cloud and container metadata hostnames/IPs
BLOCKED_HOSTNAMES: Set[str] = {
    "localhost",
    "metadata.google.internal",
    "instance-data",
    "db",
    "redis",
    "verinews_db",
    "verinews_redis",
    "verinews_backend",
}

BLOCKED_IP_STRINGS: Set[str] = {
    "169.254.169.254",  # AWS/GCP/Azure link-local metadata service
    "169.254.170.2",    # AWS ECS task metadata
    "100.100.100.200",  # Alibaba Cloud metadata
    "0.0.0.0",
}


def is_ip_blocked(ip_str: str) -> bool:
    """Check if an IP string belongs to private, loopback, link-local, or reserved ranges."""
    if ip_str in BLOCKED_IP_STRINGS:
        return True

    try:
        ip = ipaddress.ip_address(ip_str)
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        )
    except ValueError:
        # Not an IP literal (e.g. domain name)
        return False


async def validate_url_ssrf(url: str) -> str:
    """
    Validates a submitted URL against SSRF vulnerabilities:
    - Enforces http/https schemes only.
    - Blocks loopback, internal Docker networks, RFC 1918 private subnets,
      and cloud metadata IP addresses.
    - Resolves hostnames via DNS and validates all returned IPs.
    """
    if not url or not isinstance(url, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid URL provided",
        )

    url_clean = url.strip()
    try:
        parsed = urlparse(url_clean)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Malformed URL structure",
        )

    if parsed.scheme.lower() not in {"http", "https"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"URL scheme '{parsed.scheme}' is not allowed. Only HTTP and HTTPS are permitted.",
        )

    hostname = parsed.hostname
    if not hostname:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL must contain a valid hostname",
        )

    hostname_lower = hostname.lower().strip()

    # Direct blocked hostnames check
    if hostname_lower in BLOCKED_HOSTNAMES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SSRF Blocked: Access to internal host is forbidden",
        )

    # Check if hostname itself is an IP literal and blocked
    if is_ip_blocked(hostname_lower):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SSRF Blocked: Access to private or restricted IP address is forbidden",
        )

    # Resolve hostname via DNS asynchronously to detect DNS rebinding or internal aliases
    loop = asyncio.get_running_loop()
    try:
        port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
        addr_info = await loop.run_in_executor(
            None,
            lambda: socket.getaddrinfo(hostname_lower, port, proto=socket.IPPROTO_TCP),
        )
    except socket.gaierror:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not resolve hostname '{hostname_lower}'",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"DNS resolution failure for '{hostname_lower}': {e}",
        )

    # Validate all resolved addresses
    for addr in addr_info:
        sockaddr = addr[4]
        ip_addr = sockaddr[0]
        if is_ip_blocked(ip_addr):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"SSRF Blocked: Hostname '{hostname_lower}' resolves to private/restricted IP ({ip_addr})",
            )

    return url_clean
