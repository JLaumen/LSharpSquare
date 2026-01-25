import argparse

CSV_COLUMNS = ["missing_transitions", "total_time", "queries_learning", "successful_queries_learning", "validity_query",
    "successful", ]


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


def latex_table_from_csv(path):
    import pandas as pd
    df = pd.read_csv(path)
    if "missing_transitions" not in df.columns:
        raise SystemExit("`missing_transitions` column missing in CSV")
    # Ensure expected columns exist
    for c in CSV_COLUMNS:
        if c not in df.columns:
            df[c] = pd.NA
    # Coerce numeric columns
    num_cols = [c for c in CSV_COLUMNS if c != "missing_transitions"]
    df[num_cols] = df[num_cols].apply(pd.to_numeric, errors="coerce")
    df["successful"] = df["successful"].fillna(0).astype(int)
    # Per-row percentage of successful queries (handle zero queries)
    denom = df["queries_learning"].replace(0, pd.NA)
    df["success_pct"] = (df["successful_queries_learning"] / denom).fillna(0) * 100
    # Group and aggregate
    grouped = df.groupby("missing_transitions", dropna=False)
    count = grouped.size().rename("benchmarks")
    successful = grouped["successful"].sum().rename("successful_count")
    median_total_time = grouped["total_time"].median().rename("median_total_time")
    median_queries = grouped["queries_learning"].median().rename("median_queries")
    median_validity = grouped["validity_query"].median().rename("median_validity_query")
    median_success_pct = grouped["success_pct"].median().rename("median_success_pct")
    res = pd.concat([count, successful, median_total_time, median_queries, median_validity, median_success_pct],
                    axis=1).reset_index()
    # Format numeric output
    float_cols = ["median_total_time", "median_queries", "median_validity_query", "median_success_pct"]
    res[float_cols] = res[float_cols].round(2)
    res["benchmarks"] = res["benchmarks"].astype(int)
    res["successful_count"] = res["successful_count"].astype(int)
    # Print LaTeX table
    print(res.to_latex(index=False, float_format="%.0f", na_rep="0"))


def main():
    p = argparse.ArgumentParser(description="Analyze results.csv grouped by missing_transitions")
    p.add_argument("csv", nargs="?", default="results.csv", help="path to results CSV (default: results.csv)")
    args = p.parse_args()
    latex_table_from_csv(args.csv)


if __name__ == "__main__":
    main()
