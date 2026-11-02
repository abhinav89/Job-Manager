"""Bounded direct HTTP fetching with address validation at connection time."""
import http.client
import ipaddress
import socket
import ssl
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from threading import BoundedSemaphore

_dns_workers = ThreadPoolExecutor(max_workers=2, thread_name_prefix="job-dns")
_dns_slots = BoundedSemaphore(2)
from urllib.parse import urlsplit, urljoin, quote

from bs4 import BeautifulSoup

MAX_BYTES = 2 * 1024 * 1024
MAX_TEXT = 64_000
TOTAL_SECONDS = 30


class UnsafeURL(ValueError):
    pass


def public_addresses(host: str, port: int, timeout: float = 5) -> list[str]:
    try:
        if not _dns_slots.acquire(blocking=False):
            raise UnsafeURL("Job URL resolution is busy. Try again shortly.")
        def resolve():
            try:
                return socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
            finally:
                _dns_slots.release()
        resolved = _dns_workers.submit(resolve).result(timeout=timeout)
        addresses = list(dict.fromkeys(item[4][0] for item in resolved))
    except (OSError, UnicodeError, FutureTimeout) as exc:
        raise UnsafeURL("The job URL could not be resolved.") from exc
    if not addresses:
        raise UnsafeURL("The job URL has no public address.")
    for address in addresses:
        ip = ipaddress.ip_address(address)
        ip = getattr(ip, "ipv4_mapped", None) or ip
        if not ip.is_global or ip.is_multicast or ip.is_reserved or ip.is_unspecified:
            raise UnsafeURL("The job URL must resolve only to public internet addresses.")
    return sorted(addresses, key=lambda address: ipaddress.ip_address(address).version)


def fetch_job_text(url: str) -> str:
    deadline = time.monotonic() + TOTAL_SECONDS
    def remaining_timeout():
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise UnsafeURL("Fetching the job exceeded its time limit.")
        return min(10, remaining)
    for hop in range(4):
        try:
            parsed = urlsplit(url)
            if (parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username is not None
                    or parsed.password is not None or any(c.isspace() or ord(c) < 32 for c in url)
                    or "%" in parsed.hostname):
                raise UnsafeURL("Enter a public HTTP or HTTPS job URL without credentials.")
            host = parsed.hostname.encode("idna").decode("ascii")
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            addresses = public_addresses(host, port, timeout=min(5, remaining_timeout()))
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise UnsafeURL("Fetching the job exceeded its time limit.")
            # Pin the TCP destination to the address just checked. Keep the original
            # hostname for HTTPS certificate verification/SNI and the HTTP Host header.
            connection = http.client.HTTPConnection(host, port, timeout=min(10, remaining))
            sock = socket.create_connection((addresses[0], port), timeout=min(10, remaining))
            if parsed.scheme == "https":
                try:
                    sock.settimeout(remaining_timeout())
                    sock = ssl.create_default_context().wrap_socket(sock, server_hostname=host)
                except BaseException:
                    sock.close()
                    raise
            connection.sock = sock
            try:
                path = quote(parsed.path or "/", safe="/%:@!$&'()*+,;=-._~")
                if parsed.query:
                    path += "?" + quote(parsed.query, safe="%/?@!$&'()*+,;=:-._~")
                sock.settimeout(remaining_timeout())
                connection.request("GET", path, headers={"Accept-Encoding": "identity", "User-Agent": "CVTailor/1.0"})
                sock.settimeout(remaining_timeout())
                response = connection.getresponse()
                if response.status in {301, 302, 303, 307, 308}:
                    target = response.getheader("Location")
                    if not target or hop == 3:
                        raise UnsafeURL("The job URL has too many or invalid redirects.")
                    url = urljoin(url, target)
                    continue
                if response.status != 200:
                    raise UnsafeURL(f"The job site returned HTTP {response.status}.")
                if response.getheader("Content-Encoding", "identity").lower() != "identity":
                    raise UnsafeURL("The job site ignored the uncompressed response request.")
                body = bytearray()
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise UnsafeURL("Fetching the job exceeded its time limit.")
                    sock.settimeout(min(10, remaining))
                    chunk = response.read1(min(64 * 1024, MAX_BYTES + 1 - len(body)))
                    if not chunk:
                        break
                    body.extend(chunk)
                    if len(body) > MAX_BYTES:
                        raise UnsafeURL("The job page exceeds the response size limit.")
            finally:
                connection.close()
            soup = BeautifulSoup(bytes(body), "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                tag.decompose()
            return soup.get_text(" ", strip=True)[:MAX_TEXT]
        except UnsafeURL:
            raise
        except (OSError, ValueError, http.client.HTTPException) as exc:
            raise UnsafeURL("The job URL could not be fetched safely.") from exc
    raise UnsafeURL("The job URL could not be fetched safely.")
