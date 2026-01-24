import argparse
import sys

CSV_COLUMNS = [
    "missing_transitions",
    "total_time",
    "queries_learning",
    "successful_queries_learning",
    "validity_query",
    "successful",
]

def analyze_with_pandas(path):
    import pandas as pd
    df = pd.read_csv(path)
    if "missing_transitions" not in df.columns:
        raise SystemExit("`missing_transitions` column missing in CSV")
    # Ensure all expected columns exist
    for c in CSV_COLUMNS:
        if c not in df.columns:
            df[c] = pd.NA
    # Coerce numeric columns
    num_cols = [c for c in CSV_COLUMNS if c != "missing_transitions"]
    df[num_cols] = df[num_cols].apply(pd.to_numeric, errors="coerce")
    df["successful"] = df["successful"].fillna(0).astype(int)
    grouped = df.groupby("missing_transitions", dropna=False)
    count = grouped.size().rename("benchmarks")
    successful = grouped["successful"].sum().rename("successful_count")
    medians = grouped[num_cols].median().rename(lambda x: f"median_{x}")
    res = pd.concat([count, successful, medians], axis=1).reset_index()
    # Format floats
    float_cols = [c for c in res.columns if c.startswith("median_")]
    res[float_cols] = res[float_cols].round(4)
    # Round everything to integer
    int_cols = [c for c in res.columns if c not in float_cols + ["missing_transitions"]]
    res[int_cols] = res[int_cols].fillna(0).astype(int)
    print(res.to_string(index=False))


def main():
    p = argparse.ArgumentParser(description="Analyze results.csv grouped by missing_transitions")
    p.add_argument("csv", nargs="?", default="results.csv", help="path to results CSV (default: results.csv)")
    args = p.parse_args()
    import pandas
    analyze_with_pandas(args.csv)

if __name__ == "__main__":
    main()