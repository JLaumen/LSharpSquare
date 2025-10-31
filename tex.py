import pandas as pd
import math

CSV_PATH = "benchmarking/results/benchmark_all.csv"

def to_bool(x):
    if pd.isna(x):
        return False
    if isinstance(x, bool):
        return x
    s = str(x).strip().lower()
    if s in {"true", "yes", "y", "1"}:
        return True
    try:
        return float(s) != 0.0
    except Exception:
        return False

def main():
    df = pd.read_csv(CSV_PATH, dtype=str)
    if "file name" not in df.columns:
        raise SystemExit("CSV missing `file name` column")

    # group key: first 11 characters
    df["group"] = df["file name"].astype(str).str[:11]

    # numeric normalize
    df["automaton_size_num"] = pd.to_numeric(df.get("automaton_size", pd.Series(["0"] * len(df))), errors="coerce").fillna(0).astype(int)
    df["succeeded_raw"] = df.get("succeeded", pd.Series(["False"] * len(df)))
    df["time_raw"] = df.get("total_time", pd.Series([None] * len(df)))

    # success condition
    df["is_success"] = df.apply(
        lambda r: (r["automaton_size_num"] != 0)
        and to_bool(r["succeeded_raw"])
        and not pd.isna(r["time_raw"])
        and float(r["time_raw"]) < 200,
        axis=1,
    )

    # columns to average
    avg_cols = ["automaton_size", "total_time", "queries_learning", "validity_query"]

    rows = []
    for name, group in df.groupby("group", sort=True):
        total = len(group)
        succ_group = group[group["is_success"]]
        succ_count = len(succ_group)

        # Compute means even if succ_count == 0 (to show 0/n rows)
        means = {}
        for col in avg_cols:
            vals = pd.to_numeric(
                succ_group.get(col, pd.Series([math.nan] * len(succ_group))),
                errors="coerce"
            )
            means[col] = vals.mean()

        dfa_size = name[-2:]  # last two chars of group name

        rows.append({
            "dfa_size": dfa_size,
            "succeeded": succ_count,
            "total": total,
            "automaton_size": means["automaton_size"],
            "total_time": means["total_time"],
            "queries_learning": means["queries_learning"],
            "validity_query": means["validity_query"],
        })

    out_df = pd.DataFrame(rows).sort_values(by="dfa_size")

    # print LaTeX table
    print("\\begin{tabular}{lrrrrr}")
    print("\\toprule")
    print("DFA Size & Succeeded / Total & Mean Automaton Size & Mean Total Time & Mean Queries Learning & Mean Validity Query \\\\")
    print("\\midrule")

    for _, row in out_df.iterrows():
        size = row["dfa_size"]
        succ_ratio = f"{row['succeeded']}/{row['total']}"
        auto_size = f"{row['automaton_size']:.2f}" if not pd.isna(row["automaton_size"]) else "n/a"
        total_time = f"{row['total_time']:.2f}" if not pd.isna(row["total_time"]) else "n/a"
        queries_learning = f"{row['queries_learning']:.2f}" if not pd.isna(row["queries_learning"]) else "n/a"
        validity_query = f"{row['validity_query']:.2f}" if not pd.isna(row["validity_query"]) else "n/a"
        print(f"{size} & {succ_ratio} & {auto_size} & {total_time} & {queries_learning} & {validity_query} \\\\")

    print("\\bottomrule")
    print("\\end{tabular}")

if __name__ == "__main__":
    main()
