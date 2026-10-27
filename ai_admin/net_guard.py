"""SSRF-safe network guard and provider content fetcher."""

import ipaddress
import socket
import urllib.parse
from typing import List, Optional, Set, Tuple

# Approved outbound provider hostnames
APPROVED_PROVIDER_HOSTS: Set[str] = {
    "image.tmdb.org",
    "api.themoviedb.org",
    "api.opensubtitles.com",
    "api.subdl.com",
    "dl.subdl.com",
    "malayalamsubtitles.org",
    "subtitles.strem.io",
    "opensubtitles-v3.strem.io",
    "webservice.fanart.tv",
    "assets.fanart.tv",
    "v3-cinemeta.strem.io",
    "images.metahub.space",
    "m.media-amazon.com",
    "ia.media-imdb.com",
    "api.tvmaze.com",
    "static.tvmaze.com",
}


def is_ip_private_or_restricted(ip_str: str) -> bool:
    """Check whether an IP address belongs to loopback, private, link-local, or reserved ranges."""
    try:
        ip = ipaddress.ip_address(ip_str)
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        )
    except ValueError:
        return True


def validate_outbound_url(
    url: str,
    allowed_hosts: Optional[Set[str]] = None,
    allow_all_public_https: bool = False,
) -> Tuple[bool, str]:
    """Validate a remote URL against scheme, domain allowlist, and IP restrictions."""
    if not url or not isinstance(url, str):
        return False, "Empty or invalid URL."

    try:
        parsed = urllib.parse.urlsplit(url)
    except Exception:
        return False, "Malformed URL."

    # 1. Scheme must be strict HTTPS
    if parsed.scheme.lower() != "https":
        return False, "Insecure protocol: only HTTPS is permitted."

    hostname = (parsed.hostname or "").lower()
    if not hostname:
        return False, "Missing hostname in URL."

    # 2. Hostname allowlist check
    active_allowlist = allowed_hosts if allowed_hosts is not None else APPROVED_PROVIDER_HOSTS
    if not allow_all_public_https and hostname not in active_allowlist:
        # Check wildcard subdomains
        matched = any(hostname.endswith("." + allowed) for allowed in active_allowlist)
        if not matched:
            return False, f"Destination host '{hostname}' is not in approved provider allowlist."

    # 3. DNS resolution & IP check (SSRF prevention)
    try:
        addr_info = socket.getaddrinfo(hostname, 443, family=socket.AF_UNSPEC, type=socket.SOCK_STREAM)
        if not addr_info:
            return False, f"Could not resolve host '{hostname}'."

        for item in addr_info:
            ip_str = item[4][0]
            if is_ip_private_or_restricted(ip_str):
                return False, f"Resolved IP '{ip_str}' is in a private, loopback, or reserved range."

    except socket.gaierror as e:
        return False, f"DNS resolution failed for '{hostname}': {e}"
    except Exception as e:
        return False, f"Network security check error: {e}"

    return True, "valid_url"
