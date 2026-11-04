from __future__ import annotations

import argparse
from pathlib import Path

from source_ingest_common import (
    DownloadedAsset,
    fetch_binary,
    fetch_text,
    parse_anchors,
    read_manifest,
    safe_filename_from_url,
    slugify,
    write_binary,
    write_report,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download Mutopia reference assets for the Bach cello-suite source profile.")
    parser.add_argument(
        "--manifest",
        default="data/sources/symbolic/mutopia/manifest.csv",
        help="CSV manifest describing Mutopia source pages.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/sources/symbolic/mutopia",
        help="Directory where Mutopia assets will be written.",
    )
    parser.add_argument("--dry-run", action="store_true", help="List actions without downloading files.")
    return parser.parse_args()


def preferred_mutopia_assets(anchors: list[dict[str, str]], preferred_assets: str) -> list[dict[str, str]]:
    requested = preferred_assets.split("|")
    chosen: list[dict[str, str]] = []
    for requested_asset in requested:
        asset_key = requested_asset.strip().lower()
        candidate = None
        for anchor in anchors:
            href = anchor["href"].lower()
            text = anchor["text"].lower()
            if asset_key == "lilypond_zip" and href.endswith(".zip") and (".ly" in text or "lilypond" in text):
                candidate = anchor
                break
            if asset_key == "midi_zip" and href.endswith(".zip") and ".mid" in text:
                candidate = anchor
                break
            if asset_key == "a4_pdf" and "a4" in text and (href.endswith(".pdf") or (href.endswith(".zip") and ".pdf" in text)):
                candidate = anchor
                break
            if asset_key == "lilypond" and (href.endswith(".ly") or href.endswith(".ily")):
                candidate = anchor
                break
            if asset_key == "midi" and href.endswith(".mid"):
                candidate = anchor
                break
        if candidate is not None:
            chosen.append(candidate)
    return chosen


def main() -> None:
    args = parse_args()
    manifest_path = Path(args.manifest).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    report_path = output_dir / "ingest_report.json"

    assets: list[DownloadedAsset] = []
    for row in read_manifest(manifest_path):
        prelude_id = row["prelude_id"]
        piece_url = row["piece_info_url"]
        preferred_assets = row["preferred_assets"]
        target_dir = output_dir / prelude_id
        try:
            html = fetch_text(piece_url)
            anchors = parse_anchors(piece_url, html)
            selected_anchors = preferred_mutopia_assets(anchors, preferred_assets)
        except Exception as exc:
            assets.append(
                DownloadedAsset(
                    prelude_id=prelude_id,
                    source_url=piece_url,
                    output_path=target_dir,
                    asset_label="mutopia_assets",
                    status="failed",
                    note=f"{row['notes']} | {type(exc).__name__}: {exc}",
                )
            )
            print(f"failed {prelude_id}: {exc}")
            continue

        if not selected_anchors:
            assets.append(
                DownloadedAsset(
                    prelude_id=prelude_id,
                    source_url=piece_url,
                    output_path=target_dir,
                    asset_label="mutopia_assets",
                    status="not_found",
                    note=f"No preferred assets matched: {preferred_assets}",
                )
            )
            print(f"no assets matched for {prelude_id}")
            continue

        for anchor in selected_anchors:
            href = anchor["href"]
            label = anchor["text"] or slugify(Path(href).name)
            filename = safe_filename_from_url(href, f"{prelude_id}_{slugify(label)}")
            output_path = target_dir / filename

            if args.dry_run:
                assets.append(
                    DownloadedAsset(
                        prelude_id=prelude_id,
                        source_url=href,
                        output_path=output_path,
                        asset_label=label,
                        status="dry_run",
                        note=row["notes"],
                    )
                )
                print(f"would download {prelude_id} -> {output_path.relative_to(output_dir)}")
                continue

            try:
                payload = fetch_binary(href)
                write_binary(output_path, payload)
                assets.append(
                    DownloadedAsset(
                        prelude_id=prelude_id,
                        source_url=href,
                        output_path=output_path,
                        asset_label=label,
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
                        asset_label=label,
                        status="failed",
                        note=f"{row['notes']} | {type(exc).__name__}: {exc}",
                    )
                )
                print(f"failed {prelude_id} asset {label}: {exc}")

    write_report(report_path, assets)
    print(f"wrote report: {report_path}")


if __name__ == "__main__":
    main()
