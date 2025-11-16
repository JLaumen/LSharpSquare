# python
import argparse
import csv
import os
from pathlib import Path

def strip_first_col(input_path: Path, backup: bool = True):
    tmp_path = input_path.with_suffix(input_path.suffix + ".tmp")
    bak_path = input_path.with_suffix(input_path.suffix + ".bak")

    if backup:
        if bak_path.exists():
            bak_path.unlink()
        input_path.replace(bak_path)
        source_path = bak_path
    else:
        source_path = input_path

    with source_path.open("r", newline="", encoding="utf-8") as src, \
         tmp_path.open("w", newline="", encoding="utf-8") as dst:
        reader = csv.reader(src)
        writer = csv.writer(dst)

        for i, row in enumerate(reader):
            if i == 0:
                writer.writerow(row)  # keep first row as-is
            else:
                if row:
                    row[0] = row[0][14:]  # remove first 14 chars (results '' if shorter)
                writer.writerow(row)

    # replace original file with modified tmp (if we moved original to .bak, put tmp back to original name)
    tmp_path.replace(input_path)

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Strip first 14 chars from first CSV column (except first row).")
    p.add_argument("csv", nargs="?", default="benchmarking/results/nerode_benchmarks.csv", help="Path to CSV file")
    p.add_argument("--no-backup", action="store_true", help="Don't create a .bak backup (overwrites in-place)")
    args = p.parse_args()

    path = Path(args.csv)
    if not path.exists():
        raise SystemExit(f"File not found: `{path}`")
    strip_first_col(path, backup=not args.no_backup)
    print(f"Updated `{path}` (backup created as `{path.with_suffix(path.suffix + '.bak')}`)" )