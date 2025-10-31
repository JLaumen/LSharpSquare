# python
import re
import pandas as pd
import matplotlib.pyplot as plt

CSV_PATH = "benchmarking/results/benchmark_all.csv"
OUT_PNG = "benchmark_total_time_by_suffix.png"

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

def parse_suffix_to_int(name: str):
    if not isinstance(name, str):
        return None
    # take the last two characters as-is (do not remove underscores)
    last_two = name[9:11] if len(name) >= 2 else name
    return (int(last_two) if last_two[0] != "0" else int(last_two))

def main():
    df = pd.read_csv(CSV_PATH, dtype=str)
    if "file name" not in df.columns:
        raise SystemExit("CSV missing `file name` column")

    df["automaton_size_num"] = pd.to_numeric(df.get("automaton_size", pd.Series(["0"]*len(df))), errors="coerce").fillna(0).astype(int)
    df["succeeded_raw"] = df.get("succeeded", pd.Series(["False"]*len(df)))
    df["time_raw"] = df.get("total_time", pd.Series([None]*len(df)))
    df["is_success"] = df.apply(lambda r: (r["automaton_size_num"] != 0) and to_bool(r["succeeded_raw"]) and float(r["time_raw"]) < 200, axis=1)

    df_succ = df[df["is_success"]].copy()
    if df_succ.empty:
        print("No succeeded rows found.")
        return

    df_succ["suffix_x"] = df_succ["file name"].apply(parse_suffix_to_int)
    df_succ["total_time_num"] = pd.to_numeric(df_succ.get("total_time", pd.Series([None]*len(df_succ))), errors="coerce")

    plot_df = df_succ.dropna(subset=["suffix_x", "total_time_num"])
    if plot_df.empty:
        print("No rows with valid suffix and total_time to plot.")
        return

    x = plot_df["suffix_x"].astype(int)
    y = plot_df["total_time_num"].astype(float)

    # plt.style.use("seaborn-whitegrid")
    plt.figure(figsize=(9, 5))
    sc = plt.scatter(x, y, alpha=1, s=5, linewidths=0.6)
    plt.yscale("log")
    plt.xlabel("Suffix (last two chars of `file_name`)")
    plt.ylabel("total_time (log scale)")
    plt.title("Total Time vs. File Suffix (succeeded items only)")
    plt.grid(True, linestyle="--", alpha=0.3)
    # cbar = plt.colorbar(sc)
    # cbar.set_label("suffix (numeric)")
    plt.tight_layout()
    plt.savefig(OUT_PNG, dpi=150)
    print(f"Saved plot to `{OUT_PNG}`")
    plt.show()

if __name__ == "__main__":
    main()