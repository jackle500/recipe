"""URL + video extraction. Returns dicts, NO SQL."""

import ipaddress
import socket
from urllib.parse import urlparse


def guard_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Only http/https allowed")

    ips = socket.getaddrinfo(parsed.hostname, 443)
    # Each entry is (faminly, proto, canonname, (addr, port))
    # Extract addr from Each

    for ip in ips:
        addr = ipaddress.ip_address(ip[4][0])
        if addr.is_private:  # 10.x, 172.16-31.x, 192.168.x
            raise ValueError("private IP not allowed")
        if addr.is_loopback:  # 127.x
            raise ValueError("loopback IP not allowed")
        if addr.is_link_local:  # 169.254.x
            raise ValueError("link-local IP not allowed")
        if addr.is_multicast:  # 224-239.x
            raise ValueError("muticast IP not allowed")
        if addr.is_reserved:
            raise ValueError("reserved IP not allow")
        network = ipaddress.ip_network("100.64.0.0/10")
        if addr in network:
            raise ValueError("CGNAT range")


def split_qty(raw: str) -> tuple[str, str]:
    raise NotImplementedError("P2.1")


def from_page(url: str) -> dict:
    raise NotImplementedError("P2.2")


def from_video(url: str) -> dict:
    raise NotImplementedError("P2.5")


def is_video(url: str) -> bool:
    raise NotImplementedError("P2.6")
