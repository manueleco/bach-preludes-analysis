from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run all external source-profile ingestion scripts.")
    parser.add_argument("--dry-run", action="store_true", help="Pass dry-run to each profile ingester.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    script_names = [
        "ingest_kern_sources.py",
        "ingest_mutopia_sources.py",
        "ingest_musopen_sources.py",
    ]

    for script_name in script_names:
        command = [sys.executable, str(repo_root / "scripts" / script_name)]
        if args.dry_run:
            command.append("--dry-run")
        print(f"running {' '.join(command)}")
        subprocess.run(command, cwd=repo_root, check=True)


if __name__ == "__main__":
    main()
