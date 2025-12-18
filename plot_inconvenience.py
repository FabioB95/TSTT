
import argparse, re, math, numpy as np, pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt

# ===================== CONFIG =====================
FILE_GLOB = "solution_*.xlsx"
SHEET_SUMMARY_CANDIDATES = ["Summary", "Foglio1", "Foglio 1", "Sheet1"]
SHEET_ASSIGNMENTS_CANDIDATES = ["Assignments", "Foglio2", "Foglio 'Assignments'"]

# Totale veicoli atteso per taglia (denominatore fisso per medie pesate)
EXPECTED_VEHICLES = {
    100:   38773,
    250:   460367,
    500:   926697,
    1000:  3778544,
    2000:  14800953,
}

# === CLASSIFICATION (per richiesta utente) ===
# - Se il nome contiene "null_benchmark_balanced_random_departure" → Benchmark-Random
# - Altrimenti, se contiene "dataset_" → Benchmark-Fixed (traffic = no/low/medium/high da substring)
# - Altrimenti → Optimization
TRAFFIC_MAP = {
    "no": r"(no[_\- ]?traffic|notraffic|ff\b|free[_\- ]?flow|zero)",
    "low": r"(low[_\- ]?traffic|traffic[_\- ]?low|\blow\b|_lt_|-lt-)",
    "medium": r"(med(iu)?m[_\- ]?traffic|traffic[_\- ]?medium|\bmedium\b|_mt_|-mt-)",
    "high": r"(high[_\- ]?traffic|traffic[_\- ]?high|\bhigh\b|_ht_|-ht-)",
}

# ===================== UTILS =====================
def weighted_mean(values, weights, denom_fixed: float | None = None) -> float:
    v = np.asarray(values, dtype=float)
    w = np.asarray(weights, dtype=float)
    num = float(np.nansum(v * w))
    den = float(denom_fixed if (denom_fixed is not None and np.isfinite(denom_fixed) and denom_fixed>0) else np.nansum(w))
    return float(num/den) if den>0 else float("nan")

def normalize_columns(df: pd.DataFrame) -> dict:
    return {c.strip().lower(): c for c in df.columns}

def classify_file(fname: str) -> tuple[str,str]:
    s = fname.lower()
    if "null_benchmark_balanced_random_departure" in s:
        return "Benchmark-Random", "n/a"
    if "dataset_" in s:
        # Benchmark-Fixed
        traffic = "n/a"
        for lvl, pat in TRAFFIC_MAP.items():
            if re.search(pat, s):
                traffic = lvl
                break
        return "Benchmark-Fixed", traffic
    # default
    return "Optimization", "n/a"

def detect_size_from_name_or_summary(fname: str, summary_df: pd.DataFrame | None) -> int | None:
    if summary_df is not None:
        cols = normalize_columns(summary_df)
        idcol = cols.get("id trip")
        if idcol and summary_df[idcol].notna().any():
            vals = sorted(pd.unique(summary_df[idcol].dropna().astype(int)))
            if len(vals)==1:
                return int(vals[0])
    for size in [2000,1000,500,250,100]:
        if str(size) in fname:
            return size
    return None

# ===================== LOADERS =====================
def read_summary(xlsx: Path) -> pd.DataFrame | None:
    for sh in SHEET_SUMMARY_CANDIDATES:
        try:
            df = pd.read_excel(xlsx, sheet_name=sh)
            if isinstance(df, pd.DataFrame) and not df.empty:
                return df
        except Exception:
            continue
    return None

def read_assignments(xlsx: Path) -> pd.DataFrame | None:
    for sh in SHEET_ASSIGNMENTS_CANDIDATES:
        try:
            df = pd.read_excel(xlsx, sheet_name=sh)
            if isinstance(df, pd.DataFrame) and not df.empty:
                return df
        except Exception:
            continue
    try:
        return pd.read_excel(xlsx, sheet_name="Assignments")
    except Exception:
        return None

# ===================== CORE COMPUTATION =====================
def compute_weighted_metrics_from_assignments(dfA: pd.DataFrame, expected_total: float | None) -> dict:
    cols = normalize_columns(dfA)
    trip = cols.get("trip_id")
    veh  = cols.get("vehicles")
    ff   = cols.get("freeflowtime_min")
    rt   = cols.get("realttraveltime_min") or cols.get("realtraveltime_min")
    if rt is None:
        for c in dfA.columns:
            if c.strip().lower() in ("realtraveltime_min","realttraveltime_min","realtraveltime_minuti"):
                rt = c; break
    missing = [n for n in ["trip_id","vehicles","freeflowtime_min","realtraveltime_min"] if locals().get(n[:2] if n=="trip_id" else n[:2]) is None]
    if trip is None or veh is None or ff is None or rt is None:
        raise ValueError("Assignments missing required columns (need Trip_ID, Vehicles, FreeFlowTime_min, RealTravelTime_min).")

    df = dfA.copy()
    df["Final_Inconv_Row"] = df[rt] / df[ff]
    ff_min = df.groupby(trip)[ff].transform("min").replace(0, np.nan)
    df["FF_Inconv_Row"] = df[ff] / ff_min

    denom = expected_total if expected_total and np.isfinite(expected_total) else None
    w_final = weighted_mean(df["Final_Inconv_Row"], df[veh], denom_fixed=denom)
    w_ff    = weighted_mean(df["FF_Inconv_Row"],    df[veh], denom_fixed=denom)
    return {
        "weighted_final_inconv": w_final,
        "weighted_ff_inconv": w_ff,
        "vehicles_sum": float(df[veh].sum()),
        "rows": int(len(df)),
        "unique_trips": int(pd.Series(df[trip]).nunique())
    }

def extract_summary_inconv(summary_df: pd.DataFrame) -> float | None:
    cols = normalize_columns(summary_df)
    col = cols.get("inconvenience ave") or cols.get("inconvenience_ave") or cols.get("inconvenience")
    if col is None:
        for c in summary_df.columns:
            s = c.strip().lower()
            if "inconvenience" in s and ("ave" in s or "mean" in s or "avg" in s):
                col = c; break
    if col is None:
        return None
    vals = pd.to_numeric(summary_df[col], errors="coerce").dropna()
    if len(vals)==0: return None
    if len(vals)==1: return float(vals.iloc[0])
    return float(vals.mean())

# ===================== MAIN =====================
def main():
    ap = argparse.ArgumentParser(description="Unified inconvenience report (Summary vs recomputed from Assignments)")
    ap.add_argument("--dir", type=str, default=".", help="Directory to scan")
    ap.add_argument("--pattern", type=str, default=FILE_GLOB, help="Glob for solution files")
    ap.add_argument("--out", type=str, default="inconv_out", help="Output folder")
    args = ap.parse_args()

    in_dir = Path(args.dir)
    out_dir = Path(args.out); out_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(in_dir.rglob(args.pattern))
    if not files:
        print(f"⚠️ No files matching {args.pattern} in {in_dir.resolve()}")
        return

    rows = []
    for i, f in enumerate(files, 1):
        print(f"[{i}/{len(files)}] {f.name}")
        scenario, traffic = classify_file(f.name)

        summary_df = read_summary(f)
        if summary_df is None:
            print("  → skip: missing Summary sheet")
            continue

        size = detect_size_from_name_or_summary(f.name, summary_df)
        expected_total = EXPECTED_VEHICLES.get(size)

        summary_inconv = extract_summary_inconv(summary_df)

        assignments_df = read_assignments(f)
        calc_final = calc_ff = veh_sum = np.nan
        if assignments_df is not None and not assignments_df.empty:
            try:
                met = compute_weighted_metrics_from_assignments(assignments_df, expected_total)
                calc_final = met["weighted_final_inconv"]
                calc_ff = met["weighted_ff_inconv"]
                veh_sum = met["vehicles_sum"]
            except Exception as e:
                print(f"  ⚠️ cannot compute from Assignments: {e}")

        rows.append({
            "file": f.name,
            "scenario": scenario,
            "traffic": traffic,
            "trip_size": size,
            "vehicles_expected": expected_total,
            "vehicles_sum": veh_sum,
            "summary_inconv": summary_inconv,
            "calc_final_inconv_weighted": calc_final,
            "calc_ff_inconv_weighted": calc_ff,
            "delta_calc_vs_summary": (calc_final - summary_inconv) if (summary_inconv is not None and np.isfinite(calc_final)) else np.nan,
        })

    df = pd.DataFrame(rows).sort_values(["scenario","traffic","trip_size","file"])
    out_xlsx = out_dir / "MASTER_inconvenience_report.xlsx"
    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as xl:
        df.to_excel(xl, sheet_name="PerFile", index=False)

        # Aggregates by (scenario, traffic)
        def agg_weighted(group: pd.DataFrame):
            w = group["vehicles_expected"].fillna(group["vehicles_sum"]).replace(0, np.nan)
            return pd.Series({
                "files": len(group),
                "sum_expected_veh": float(w.sum(skipna=True)),
                "summary_inconv_mean": weighted_mean(group["summary_inconv"], w),
                "calc_final_inconv_mean": weighted_mean(group["calc_final_inconv_weighted"], w),
                "calc_ff_inconv_mean": weighted_mean(group["calc_ff_inconv_weighted"], w),
            })
        agg = df.groupby(["scenario","traffic"], dropna=False).apply(agg_weighted).reset_index()
        agg.to_excel(xl, sheet_name="Aggregates", index=False)

        diffs = df[["file","scenario","traffic","trip_size","summary_inconv","calc_final_inconv_weighted","delta_calc_vs_summary","vehicles_sum","vehicles_expected"]]
        diffs.to_excel(xl, sheet_name="Diffs_Summary_vs_Calc", index=False)

    # Plot
    labels = []
    for _, r in agg.iterrows():
        if r["scenario"] == "Benchmark-Fixed":
            labels.append(f"{r['scenario']} ({r['traffic']})")
        else:
            labels.append(r["scenario"])
    x = np.arange(len(labels))
    w = 0.28
    plt.figure(figsize=(max(8, 1.2*len(labels)), 6))
    plt.bar(x - w, agg["summary_inconv_mean"], width=w, label="Summary inconvenience")
    plt.bar(x,     agg["calc_final_inconv_mean"], width=w, label="Recomputed final (weighted)")
    plt.bar(x + w, agg["calc_ff_inconv_mean"], width=w, label="FF-based (weighted)")
    plt.xticks(x, labels, rotation=20, ha="right")
    plt.ylabel("Weighted inconvenience (ratio)")
    plt.title("Inconvenience comparison by scenario (weighted by expected vehicles)")
    plt.legend()
    plt.tight_layout()
    out_png = out_dir / "aggregates_inconvenience_comparison.png"
    plt.savefig(out_png, dpi=160)
    plt.close()

    print(f"✅ Done. Excel: {out_xlsx}")
    print(f"🖼️ Plot:  {out_png}")

if __name__ == "__main__":
    main()
