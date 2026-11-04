from __future__ import annotations

import argparse
from pathlib import Path

from source_ingest_common import (
    DownloadedAsset,
    fetch_binary,
    fetch_binary_via_curl,
    fetch_text,
    fetch_text_via_curl,
    parse_anchors,
    read_manifest,
    safe_filename_from_url,
    write_binary,
    write_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download Musopen score PDFs for the Bach cello-suite source profile.")
    parser.add_argument(
        "--manifest",
        default="data/sources/symbolic/musopen/manifest.csv",
        help="CSV manifest describing Musopen score pages.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/sources/symbolic/musopen",
        help="Directory where Musopen assets will be written.",
    )
    parser.add_argument("--dry-run", action="store_true", help="List actions without downloading files.")
    return parser.parse_args()


def choose_musopen_pdf(anchors: list[dict[str, str]]) -> dict[str, str] | None:
    pdf_anchors = [anchor for anchor in anchors if "dl.musopen.org" in anchor["href"] and anchor["href"].lower().endswith(".pdf")]
    if not pdf_anchors:
        return None

    for anchor in pdf_anchors:
        href_lower = anchor["href"].lower()
        text_lower = anchor["text"].lower()
        if "prelude" in href_lower or "prelude" in text_lower:
            return anchor
    return pdf_anchors[0]


def main() -> None:
    args = parse_args()
    manifest_path = Path(args.manifest).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    report_path = output_dir / "ingest_report.json"

    assets: list[DownloadedAsset] = []
    for row in read_manifest(manifest_path):
        prelude_id = row["prelude_id"]
        page_url = row["page_url"]
        target_dir = output_dir / prelude_id
        page_headers = {
            "Referer": page_url,
            "Origin": "https://musopen.org",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        binary_headers = {
            "Referer": page_url,
            "Origin": "https://musopen.org",
            "Accept": "application/pdf,*/*;q=0.8",
        }
        try:
            try:
                html = fetch_text(page_url, extra_headers=page_headers)
            except Exception:
                html = fetch_text_via_curl(page_url, extra_headers=page_headers)
            anchors = parse_anchors(page_url, html)
            selected_anchor = choose_musopen_pdf(anchors)
        except Exception as exc:
            assets.append(
                DownloadedAsset(
                    prelude_id=prelude_id,
                    source_url=page_url,
                    output_path=target_dir,
                    asset_label="musopen_pdf",
                    status="failed",
                    note=f"{row['notes']} | {type(exc).__name__}: {exc}",
                )
            )
            print(f"failed {prelude_id}: {exc}")
            continue

        if selected_anchor is None:
            lowered_html = html.lower()
            note = "No downloadable Musopen PDF link was found on the page."
            if "cloudflare" in lowered_html or "cf-mitigated" in lowered_html or "just a moment" in lowered_html:
                note = "Musopen page appears to be blocked by a Cloudflare challenge for non-browser access."
            assets.append(
                DownloadedAsset(
                    prelude_id=prelude_id,
                    source_url=page_url,
                    output_path=target_dir,
                    asset_label="musopen_pdf",
                    status="not_found",
                    note=note,
                )
            )
            print(f"no PDF found for {prelude_id}: {note}")
            continue

        href = selected_anchor["href"]
        filename = safe_filename_from_url(href, f"{prelude_id}.pdf")
        output_path = target_dir / filename

        if args.dry_run:
            assets.append(
                DownloadedAsset(
                    prelude_id=prelude_id,
                    source_url=href,
                    output_path=output_path,
                    asset_label="pdf",
                    status="dry_run",
                    note=row["notes"],
                )
            )
            print(f"would download {prelude_id} -> {output_path.relative_to(output_dir)}")
            continue

        try:
            try:
                payload = fetch_binary(href, extra_headers=binary_headers)
            except Exception:
                payload = fetch_binary_via_curl(href, extra_headers=binary_headers)
            write_binary(output_path, payload)
            assets.append(
                DownloadedAsset(
                    prelude_id=prelude_id,
                    source_url=href,
                    output_path=output_path,
                    asset_label="pdf",
                    status="downloaded",
                    note=row["notes"],
                )
            )
            print(f"downloaded {prelude_id} -> {output_path.relative_to(output_dir)}")
        except Exception as exc:
            assets.append(
                DownloadedAsset(
                    prelude_id=prelude_id,
                    source_url=href,
                    output_path=output_path,
                    asset_label="pdf",
                    status="failed",
                    note=f"{row['notes']} | {type(exc).__name__}: {exc}",
                )
            )
            print(f"failed {prelude_id}: {exc}")

    write_report(report_path, assets)
    print(f"wrote report: {report_path}")


if __name__ == "__main__":
    main()
