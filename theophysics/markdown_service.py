#!/usr/bin/env python3
"""Local-only URL-to-Markdown preview and immutable versioned capture service."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from html.parser import HTMLParser
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SCHEMA_VERSION = "1.0.0"
MAX_SOURCE_BYTES = 5_000_000
PREVIEW_TTL_SECONDS = 3600


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_public_url(value: str, allow_private: bool = False) -> str:
    parsed = urllib.parse.urlsplit(value.strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username:
        raise ValueError("Only unauthenticated http(s) URLs are accepted")
    if not allow_private:
        for info in socket.getaddrinfo(parsed.hostname, parsed.port or 443):
            address = info[4][0]
            import ipaddress
            if not ipaddress.ip_address(address).is_global:
                raise ValueError("Private, loopback, and link-local destinations are blocked")
    return urllib.parse.urlunsplit(parsed)


class PublicRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        validate_public_url(new_url)
        return super().redirect_request(request, file_pointer, code, message, headers, new_url)


class MarkdownParser(HTMLParser):
    BLOCKS = {"article", "aside", "blockquote", "div", "footer", "header", "main", "nav", "p", "section", "table", "tr", "ul", "ol"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.title_parts: list[str] = []
        self.in_title = False
        self.skip_depth = 0
        self.hrefs: list[str | None] = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "template", "svg"}:
            self.skip_depth += 1
        if self.skip_depth:
            return
        if tag == "title":
            self.in_title = True
        elif re.fullmatch(r"h[1-6]", tag):
            self.parts.append("\n\n" + "#" * int(tag[1]) + " ")
        elif tag in self.BLOCKS:
            self.parts.append("\n\n")
        elif tag == "br":
            self.parts.append("\n")
        elif tag == "li":
            self.parts.append("\n- ")
        elif tag in {"strong", "b"}:
            self.parts.append("**")
        elif tag in {"em", "i"}:
            self.parts.append("*")
        elif tag == "a":
            self.parts.append("[")
            self.hrefs.append(dict(attrs).get("href"))

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "template", "svg"}:
            self.skip_depth = max(0, self.skip_depth - 1)
            return
        if self.skip_depth:
            return
        if tag == "title":
            self.in_title = False
        elif tag in {"strong", "b"}:
            self.parts.append("**")
        elif tag in {"em", "i"}:
            self.parts.append("*")
        elif tag == "a":
            href = self.hrefs.pop() if self.hrefs else None
            self.parts.append(f"]({href})" if href else "]")

    def handle_data(self, data):
        if self.skip_depth:
            return
        text = re.sub(r"\s+", " ", html.unescape(data))
        if self.in_title:
            self.title_parts.append(text)
        self.parts.append(text)

    def result(self) -> tuple[str, str]:
        title = re.sub(r"\s+", " ", "".join(self.title_parts)).strip() or "Untitled page"
        markdown = "".join(self.parts)
        markdown = re.sub(r"[ \t]+\n", "\n", markdown)
        markdown = re.sub(r"\n{3,}", "\n\n", markdown).strip()
        return title, markdown


def extract_local(url: str, allow_private: bool = False) -> dict:
    url = validate_public_url(url, allow_private)
    request = urllib.request.Request(url, headers={"User-Agent": "TheophysicsResearchCapture/1.0", "Accept": "text/html,text/plain;q=0.9"})
    retrieved_at = utc_now()
    opener = urllib.request.build_opener() if allow_private else urllib.request.build_opener(PublicRedirectHandler())
    with opener.open(request, timeout=20) as response:
        source = response.read(MAX_SOURCE_BYTES + 1)
        if len(source) > MAX_SOURCE_BYTES:
            raise ValueError("Page exceeds 5 MB capture limit")
        content_type = response.headers.get_content_type()
        charset = response.headers.get_content_charset() or "utf-8"
        final_url = response.geturl()
    text = source.decode(charset, errors="replace")
    if content_type == "text/plain":
        title, markdown = urllib.parse.urlsplit(final_url).path.rsplit("/", 1)[-1] or "Plain text", text
    elif content_type in {"text/html", "application/xhtml+xml"}:
        parser = MarkdownParser()
        parser.feed(text)
        title, markdown = parser.result()
    else:
        raise ValueError(f"Unsupported content type: {content_type}")
    if not markdown.strip():
        raise ValueError("No readable content was extracted")
    js_likely = bool(re.search(r"<div[^>]+id=[\"'](?:root|app|__next)[\"'][^>]*>\s*</div>", text, re.I)) and len(markdown) < 500
    return {
        "schemaVersion": SCHEMA_VERSION,
        "originalUrl": url,
        "finalUrl": final_url,
        "pageTitle": title,
        "retrievedAt": retrieved_at,
        "contentHash": "sha256:" + hashlib.sha256(source).hexdigest(),
        "extractionMethod": "local-http-html-parser-v1",
        "provider": "local",
        "markdown": markdown,
        "sourceReceipt": {"contentType": content_type, "byteLength": len(source), "rawSourceHash": "sha256:" + hashlib.sha256(source).hexdigest()},
        "rawSource": text,
        "warnings": ["JavaScript-rendered content may be incomplete"] if js_likely else [],
        "evidenceStatus": "UNVERIFIED EXTRACTION — NOT ADMITTED CANON",
    }


class CaptureStore:
    def __init__(self, root: Path):
        self.root = root
        self.previews: dict[str, tuple[float, dict]] = {}

    def preview(self, urls: list[str], allow_private=False) -> dict:
        if not 1 <= len(urls) <= 50:
            raise ValueError("Submit between 1 and 50 URLs")
        items = []
        for url in urls:
            try:
                capture = extract_local(url, allow_private)
                status = "review_required"
            except urllib.error.HTTPError as error:
                error.close()
                capture = {"originalUrl": url, "provider": None, "error": str(error), "fallbacks": ["crawl4ai", "jina-reader", "screenshotone"]}
                status = "failed"
            except Exception as error:
                capture = {"originalUrl": url, "provider": None, "error": str(error), "fallbacks": ["crawl4ai", "jina-reader", "screenshotone"]}
                status = "failed"
            token = str(uuid.uuid4())
            self.previews[token] = (time.time(), capture)
            items.append({"previewToken": token, "status": status, **capture})
        return {"stage": "preview", "writePerformed": False, "items": items}

    def save(self, tokens: list[str], destination: str) -> dict:
        if destination not in {"research-intake", "claim-extraction-staging"}:
            raise ValueError("Unknown destination")
        saved = []
        for token in tokens:
            created, capture = self.previews.get(token, (0, None))
            if capture is None or time.time() - created > PREVIEW_TTL_SECONDS or "error" in capture:
                raise ValueError("Preview is missing, expired, or failed")
            url_hash = hashlib.sha256(capture["originalUrl"].encode()).hexdigest()[:16]
            stamp = capture["retrievedAt"].replace(":", "-")
            version = f"{stamp}-{capture['contentHash'].split(':')[1][:12]}"
            directory = self.root / destination / url_hash / version
            directory.mkdir(parents=True, exist_ok=False)
            markdown_path = directory / "capture.md"
            receipt_path = directory / "receipt.json"
            source_path = directory / "source.html"
            markdown_path.write_text(capture["markdown"], encoding="utf-8")
            source_path.write_text(capture["rawSource"], encoding="utf-8")
            receipt = {key: value for key, value in capture.items() if key not in {"markdown", "rawSource"}}
            receipt.update({"savedAt": utc_now(), "destination": destination, "canonized": False, "files": {"markdown": str(markdown_path), "rawSource": str(source_path)}})
            receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
            saved.append({"version": version, "receiptLocation": str(receipt_path), "provider": capture["provider"]})
        return {"stage": "saved", "saved": saved, "canonized": False}


class Handler(SimpleHTTPRequestHandler):
    store: CaptureStore
    static_root: Path
    allow_private = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(self.static_root), **kwargs)

    def _json(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 100_000:
                raise ValueError("Request too large")
            data = json.loads(self.rfile.read(length))
            if self.path == "/theophysics/api/markdown/preview":
                urls = data.get("urls") or ([data["url"]] if data.get("url") else [])
                self._json(HTTPStatus.OK, self.store.preview(urls, self.allow_private))
            elif self.path == "/theophysics/api/markdown/save":
                self._json(HTTPStatus.CREATED, self.store.save(data.get("previewTokens", []), data.get("destination", "research-intake")))
            else:
                self._json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
        except Exception as error:
            self._json(HTTPStatus.BAD_REQUEST, {"error": str(error)})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--output", type=Path, default=Path("theophysics/captures"))
    parser.add_argument("--allow-private-test-urls", action="store_true", help="Tests only; disables SSRF protection")
    args = parser.parse_args()
    Handler.store = CaptureStore(args.output)
    Handler.static_root = Path("code/services-application/search-service/resources/static")
    Handler.allow_private = args.allow_private_test_urls
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Theophysics local tool: http://127.0.0.1:{args.port}/theophysics/index.html")
    server.serve_forever()


if __name__ == "__main__":
    main()
