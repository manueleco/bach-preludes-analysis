from __future__ import annotations

import argparse
from pathlib import Path

from source_ingest_common import DownloadedAsset, fetch_binary, read_manifest, write_binary, write_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download available **kern sources for the Bach cello-suite prelude profile.")
    parser.add_argument(
        "--manifest",
        default="data/sources/symbolic/kern/manifest.csv",
        help="CSV manifest describing the kern source profile.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/sources/symbolic/kern",
        help="Directory where downloaded kern files will be written.",
    )
    parser.add_argument("--dry-run", action="store_true", help="List actions without downloading files.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest_path = Path(args.manifest).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    report_path = output_dir / "ingest_report.json"

    assets: list[DownloadedAsset] = []
    for row in read_manifest(manifest_path):
        prelude_id = row["prelude_id"]
        status = row["status"]
        download_url = row["download_url"].strip()
        notes = row["notes"]

        if status != "available" or not download_url:
            asset = DownloadedAsset(
                prelude_id=prelude_id,
                source_url=row["source_page_url"],
                output_path=output_dir / f"{prelude_id}.krn",
                asset_label="krn",
                status="missing_upstream",
                note=notes,
            )
            assets.append(asset)
            print(f"skip {prelude_id}: {asset.note}")
            continue

        output_path = output_dir / f"{prelude_id}.krn"
        if args.dry_run:
            assets.append(
                DownloadedAsset(
                    prelude_id=prelude_id,
                    source_url=download_url,
                    output_path=output_path,
                    asset_label="krn",
                    status="dry_run",
                    note=notes,
                )
            )
            print(f"would download {prelude_id} -> {output_path.name}")
            continue

        try:
            payload = fetch_binary(download_url)
            write_binary(output_path, payload)
            asset = DownloadedAsset(
                prelude_id=prelude_id,
                source_url=download_url,
                output_path=output_path,
                asset_label="krn",
                status="downloaded",
                note=notes,
            )
            assets.append(asset)
            print(f"downloaded {prelude_id} -> {output_path.name}")
        except Exception as exc:
            asset = DownloadedAsset(
                prelude_id=prelude_id,
                source_url=download_url,
                output_path=output_path,
                asset_label="krn",
                status="failed",
                note=f"{notes} | {type(exc).__name__}: {exc}",
            )
            assets.append(asset)
            print(f"failed {prelude_id}: {exc}")

    write_report(report_path, assets)
    print(f"wrote report: {report_path}")


if __name__ == "__main__":
    main()
