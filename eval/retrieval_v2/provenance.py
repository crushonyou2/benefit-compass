"""Provenance helpers — platform-independent SHA256.

dev-set SHA256 is defined over UTF-8 text normalized to LF before hashing.

This makes the hash stable across Windows CRLF and Linux LF checkouts,
without relying on git show of a frozen commit object (which may not be
available in shallow CI clones).
"""
import hashlib
import pathlib


def canonical_text_bytes(path: pathlib.Path) -> bytes:
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    # SHA provenance is defined over UTF-8 text with LF line endings.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.encode("utf-8")


def canonical_text_sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(canonical_text_bytes(path)).hexdigest()
