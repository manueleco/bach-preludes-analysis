from __future__ import annotations

import csv
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen

USER_AGENT = "bach-preludes-analysis/0.1 (+https://github.com/manueleco/bach-preludes-analysis)"


class AnchorParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.anchors: list[dict[str, str]] = []
        self._current_href: str | None = None
        self._current_chunks: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "a":
            return
        attr_map = dict(attrs)
        self._current_href = attr_map.get("href")
        self._current_chunks = []

    def handle_data(self, data: str) -> None:
        if self._current_href is None:
            return
        self._current_chunks.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag != "a" or self._current_href is None:
            return
        self.anchors.append(
            {
                "href": self._current_href,
                "text": " ".join(chunk.strip() for chunk in self._current_chunks if chunk.strip()),
            }
        )
        self._current_href = None
        self._current_chunks = []


@dataclass
class DownloadedAsset:
    prelude_id: str
    source_url: str
    output_path: Path
    asset_label: str
    status: str
    note: str = ""


def _request_headers(extra_headers: dict[str, str] | None = None) -> dict[str, str]:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "*/*",
    }
    if extra_headers:
        headers.update(extra_headers)
    return headers


def fetch_text(url: str, extra_headers: dict[str, str] | None = None) -> str:
    request = Request(url, headers=_request_headers(extra_headers))
    with urlopen(request) as response:
        return response.read().decode("utf-8", errors="replace")


def fetch_binary(url: str, extra_headers: dict[str, str] | None = None) -> bytes:
    request = Request(url, headers=_request_headers(extra_headers))
    with urlopen(request) as response:
        return response.read()


def fetch_text_via_curl(url: str, extra_headers: dict[str, str] | None = None) -> str:
    command = ["curl", "-L", "--silent", "--show-error", url]
    for name, value in _request_headers(extra_headers).items():
        command.extend(["-H", f"{name}: {value}"])
    result = subprocess.run(command, check=True, capture_output=True)
    return result.stdout.decode("utf-8", errors="replace")


def fetch_binary_via_curl(url: str, extra_headers: dict[str, str] | None = None) -> bytes:
    command = ["curl", "-L", "--silent", "--show-error", url]
    for name, value in _request_headers(extra_headers).items():
        command.extend(["-H", f"{name}: {value}"])
    result = subprocess.run(command, check=True, capture_output=True)
    return result.stdout


def parse_anchors(base_url: str, html_text: str) -> list[dict[str, str]]:
    parser = AnchorParser()
    parser.feed(html_text)
    anchors: list[dict[str, str]] = []
    for anchor in parser.anchors:
        href = anchor["href"].strip()
        if not href:
            continue
        anchors.append(
            {
                "href": urljoin(base_url, href),
                "text": anchor["text"],
            }
        )
    return anchors


def safe_filename_from_url(url: str, fallback_name: str) -> str:
    parsed = urlparse(url)
    filename = Path(parsed.path).name
    return filename or fallback_name


def ensure_clean_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_binary(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def extract_zip_if_needed(archive_path: Path, extract_dir: Path) -> None:
    if archive_path.suffix.lower() != ".zip":
        return
    shutil.unpack_archive(str(archive_path), str(extract_dir))


def write_report(report_path: Path, assets: Iterable[DownloadedAsset]) -> None:
    payload = [
        {
            "prelude_id": asset.prelude_id,
            "source_url": asset.source_url,
            "output_path": str(asset.output_path),
            "asset_label": asset.asset_label,
            "status": asset.status,
            "note": asset.note,
        }
        for asset in assets
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def read_manifest(manifest_path: Path) -> list[dict[str, str]]:
    with manifest_path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return slug or "asset"
