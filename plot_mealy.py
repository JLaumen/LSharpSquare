import argparse
import sys
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

def main():
    p = argparse.ArgumentParser(description="Plot `mealy` vs `missing` from a CSV `results.txt`.")
    p.add_argument("csv", nargs="?", default="results.txt", help="Path to CSV file (default: `results.txt`).")
    p.add_argument("-o", "--out", help="Output image file (if not set, the plot will be shown).")
    args = p.parse_args()

    path = Path(args.csv)
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        sys.exit(2)

    try:
        # Let pandas infer delimiter; fallback to comma if inference fails.
        try:
            df = pd.read_csv(path, sep=None, engine="python")
        except Exception:
            df = pd.read_csv(path)
    except Exception as e:
        print(f"Failed to read CSV: {e}", file=sys.stderr)
        sys.exit(3)

    # case-insensitive column lookup
    cols = {c.lower(): c for c in df.columns}
    if "mealy" not in cols or "missing" not in cols:
        print("CSV must contain columns `mealy` and `missing` (case-insensitive).", file=sys.stderr)
        print(f"Found columns: {list(df.columns)}", file=sys.stderr)
        sys.exit(4)

    xcol = cols["mealy"]
    ycol = cols["missing"]

    x = df[xcol]
    y = df[ycol]

    # Place x values next to each other as categorical positions (preserve first-seen order)
    unique_x = pd.unique(x)
    mapping = {val: i for i, val in enumerate(unique_x)}
    x_pos = x.map(mapping)

    plt.figure(figsize=(7, 5))
    plt.scatter(x_pos, y, c="C0", alpha=1)
    plt.xlabel("Number of states")
    plt.ylabel("Number of missing transition pairs")
    plt.xticks(range(len(unique_x)), [str(v) for v in unique_x])
    plt.grid(True)
    plt.tight_layout()

    if args.out:
        plt.savefig(args.out, dpi=200)
        print(f"Saved plot to {args.out}")
    else:
        plt.show()

if __name__ == "__main__":
    main()