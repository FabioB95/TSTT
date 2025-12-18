import os, sys, math, random
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ===================== CONFIGURAZIONE =====================
INPUT_DIR   = "."                     # cartella da scansionare (usa "." o un path assoluto)
FILE_GLOB   = "solution_*.xlsx"       # pattern dei file da includere
OUT_DIR     = "batch_out"             # dove salvare tutto
U_MAX_DEFAULT = 4.0                   # usato nel TTI check se non specificato
SAMPLES_TTI   = 10                    # campioni per verifica TTI
SEED          = 42
# opzionale: mappa pattern->U_MAX (se hai scenari con U_MAX diversi)
U_MAX_BY_NAME = {
    # "high_traffic": 6.0,
    # "medium_traffic": 5.0,
    # "low_traffic": 4.0,
}
# ===========================================================

random.seed(SEED)
np.random.seed(SEED)

def weighted_mean(values, weights):
    v = np.asarray(values, dtype=float)
    w = np.asarray(weights, dtype=float)
    m = w.sum()
    return float((v*w).sum()/m) if m > 0 else float("nan")

def detect_umax_from_name(fname: str, default: float):
    name = fname.lower()
    for key, val in U_MAX_BY_NAME.items():
        if key in name:
            return float(val)
    return float(default)

def load_sheets(xls_path: Path):
    try:
        xls = pd.ExcelFile(xls_path)
    except Exception as e:
        return {"error": f"Impossibile aprire {xls_path.name}: {e}"}

    req = {}
    def try_read(sheet):
        try:
            return pd.read_excel(xls, sheet)
        except Exception:
            return None

    req["Assignments"]   = try_read("Assignments")
    req["Archi"]         = try_read("Archi")
    req["Traffic"]       = try_read("traffic dettaglio")
    req["TSTT_Debug"]    = try_read("TSTT_Debug")  # opzionale
    return req

def enrich_assignments(dfA: pd.DataFrame) -> pd.DataFrame:
    df = dfA.copy()
    for col in ["Trip_ID","Path_ID","Vehicles","FreeFlowTime_min","RealTravelTime_min","Inconvenience"]:
        if col not in df.columns:
            raise ValueError(f"Assignments: colonna mancante '{col}'")

    # shortest per Trip_ID via FF
    sp_map = df.groupby("Trip_ID")["FreeFlowTime_min"].transform("min")
    df["IsShortest"] = np.isclose(df["FreeFlowTime_min"], sp_map, rtol=1e-6, atol=1e-6)
    df["FF_ratio"]   = df["FreeFlowTime_min"] / sp_map.replace(0, np.nan)
    df = df.fillna(0)
    return df

def shares_by_path(df: pd.DataFrame):
    if "Path_ID" not in df.columns:
        return None
    g = df.groupby("Path_ID")["Vehicles"].sum().sort_index()
    tot = g.sum()
    share = (g/tot*100.0) if tot>0 else g*0
    return pd.DataFrame({"Vehicles": g, "Share_%": share})

def shares_sp_vs_nsp(df: pd.DataFrame):
    g = df.groupby("IsShortest")["Vehicles"].sum()
    tot = g.sum()
    sp = g.get(True, 0.0); nsp = g.get(False, 0.0)
    return pd.DataFrame({
        "Group": ["Shortest","Non-Shortest"],
        "Vehicles": [sp, nsp],
        "Share_%": [100*sp/tot if tot>0 else 0.0, 100*nsp/tot if tot>0 else 0.0]
    })

def weighted_metrics(df: pd.DataFrame):
    inconv_w = weighted_mean(df["Inconvenience"], df["Vehicles"])
    num = np.sum(df["Vehicles"] * (df["RealTravelTime_min"] - df["FreeFlowTime_min"]))
    den = np.sum(df["Vehicles"] * df["FreeFlowTime_min"])
    extra_w = float(num/den) if den>0 else float("nan")
    ff_w = weighted_mean(df["FF_ratio"], df["Vehicles"])
    return inconv_w, extra_w, ff_w

def save_plots(df, share_p, share_sp, out_prefix):
    # 1) Stacked bar p0/p1/p2 (se disponibile)
    if share_p is not None and not share_p.empty:
        plt.figure()
        share_p["Share_%"].plot(kind="bar")
        plt.title("Quote veicolari per Path_ID")
        plt.ylabel("Percentuale (%)")
        plt.xlabel("Path_ID")
        plt.tight_layout()
        plt.savefig(f"{out_prefix}_share_by_pathid.png", dpi=150)
        plt.close()

    # 2) Bar SP vs NSP
    plt.figure()
    share_sp.set_index("Group")["Share_%"].plot(kind="bar")
    plt.title("Quote veicolari: Shortest vs Non-Shortest")
    plt.ylabel("Percentuale (%)")
    plt.tight_layout()
    plt.savefig(f"{out_prefix}_sp_vs_nsp.png", dpi=150)
    plt.close()

    # 3) Istogramma Inconvenience pesata
    plt.figure()
    # pesiamo in modo semplice replicando ~Vehicles (cap a 200 per non esplodere)
    reps = np.clip(df["Vehicles"].round().astype(int), 1, 200)
    vals = np.repeat(df["Inconvenience"].values, reps)
    vals = vals[~np.isnan(vals)]
    plt.hist(vals, bins=30)
    plt.title("Distribuzione Inconvenience (pesata)")
    plt.xlabel("Inconvenience = TT_real / TT_FF")
    plt.ylabel("Frequenza (pesata)")
    plt.tight_layout()
    plt.savefig(f"{out_prefix}_inconvenience_hist.png", dpi=150)
    plt.close()

    # 4) Scatter FF_ratio vs Inconvenience
    plt.figure()
    plt.scatter(df["FF_ratio"], df["Inconvenience"], s=np.clip(df["Vehicles"]*2, 5, 200))
    plt.title("FF ratio vs Inconvenience (size ~ Vehicles)")
    plt.xlabel("FF_ratio (FF path / FF shortest trip)")
    plt.ylabel("Inconvenience")
    plt.tight_layout()
    plt.savefig(f"{out_prefix}_ffratio_vs_inconv.png", dpi=150)
    plt.close()

def tti_check(df_arcs, df_traf, df_tstt, n_samples, u_max) -> pd.DataFrame | None:
    if df_tstt is None or df_tstt.empty:
        return None

    if not {"Arco","Cap_15min","FFTT_min"}.issubset(df_arcs.columns):
        return None
    if not {"Arco","Tempo","Traffico Totale"}.issubset(df_traf.columns):
        return None
    if not {"i","j","t","TSTT"}.issubset(df_tstt.columns):
        return None

    arc_meta = df_arcs.set_index("Arco")[["Cap_15min","FFTT_min"]].to_dict(orient="index")

    traf = df_traf.copy()
    traf["key"] = traf["Arco"].astype(str) + "|" + traf["Tempo"].astype(int).astype(str)
    traf_map = traf.set_index("key")["Traffico Totale"].to_dict()

    dfT = df_tstt.copy()
    dfT["Arco"] = dfT["i"].astype(str) + "->" + dfT["j"].astype(str)
    dfT["Tempo"] = dfT["t"].astype(int)
    dfT["key"] = dfT["Arco"] + "|" + dfT["Tempo"].astype(str)

    rows = dfT[["key","Arco","Tempo","TSTT"]].dropna()
    if rows.empty:
        return None
    rows = rows.sample(n=min(n_samples, len(rows)), random_state=SEED)

    tti_max = 1.0 + 0.15*(u_max**4)
    out = []
    for _, r in rows.iterrows():
        key = r["key"]; arco = r["Arco"]; t = int(r["Tempo"]); tstt = float(r["TSTT"])
        meta = arc_meta.get(arco)
        flow = traf_map.get(key, np.nan)
        if (meta is None) or (not np.isfinite(flow)) or flow <= 0:
            continue
        cap = float(meta["Cap_15min"]) if np.isfinite(meta["Cap_15min"]) else None
        ff  = float(meta["FFTT_min"]) if np.isfinite(meta["FFTT_min"]) else None
        if not cap or not ff:
            continue
        u = flow / cap
        tti_teo = min(1.0 + 0.15*(u**4), tti_max)
        tti_imp = tstt / (flow * ff)
        err_abs = abs(tti_teo - tti_imp)
        err_rel = err_abs / max(tti_teo, 1e-9)
        out.append({
            "Arco": arco, "Tempo": t, "Flow_tot": flow, "Cap": cap, "FFTT": ff,
            "TTI_teo": tti_teo, "TTI_imp": tti_imp, "Err_abs": err_abs, "Err_rel": err_rel
        })
    return pd.DataFrame(out) if out else None

def analyze_one(xls_path: Path, out_base: Path) -> dict:
    sheets = load_sheets(xls_path)
    if "error" in sheets:
        return {"file": xls_path.name, "status": "error", "msg": sheets["error"]}

    dfA = sheets["Assignments"]; dfArcs = sheets["Archi"]; dfTraf = sheets["Traffic"]; dfTstt = sheets["TSTT_Debug"]

    if dfA is None or dfA.empty:
        return {"file": xls_path.name, "status": "skipped", "msg": "sheet 'Assignments' assente o vuoto"}

    # arricchisci e metriche
    try:
        dfA_enr = enrich_assignments(dfA)
    except Exception as e:
        return {"file": xls_path.name, "status": "error", "msg": f"Assignments non standard: {e}"}

    share_p   = shares_by_path(dfA_enr)
    share_sp  = shares_sp_vs_nsp(dfA_enr)
    inconv_w, extra_w, ffr_w = weighted_metrics(dfA_enr)

    # grafici
    out_base.mkdir(parents=True, exist_ok=True)
    out_prefix = str(out_base / "analysis")
    save_plots(dfA_enr, share_p, share_sp, out_prefix)

    # TTI check
    u_max = detect_umax_from_name(xls_path.name, U_MAX_DEFAULT)
    df_tti = tti_check(dfArcs, dfTraf, dfTstt, n_samples=SAMPLES_TTI, u_max=u_max)
    tti_abs = float(df_tti["Err_abs"].mean()) if df_tti is not None and not df_tti.empty else np.nan
    tti_rel = float(df_tti["Err_rel"].mean()) if df_tti is not None and not df_tti.empty else np.nan

    # report per-file
    perfile_xlsx = out_base / "analysis_report.xlsx"
    with pd.ExcelWriter(perfile_xlsx, engine="openpyxl") as xl:
        # summary
        rows = [
            {"Metrica": "Weighted Inconvenience", "Valore": inconv_w},
            {"Metrica": "Weighted Extra-Time Ratio", "Valore": extra_w},
            {"Metrica": "Weighted FF Ratio", "Valore": ffr_w},
            {"Metrica": "Share Shortest (%)", "Valore": share_sp.loc[share_sp["Group"]=="Shortest","Share_%"].values[0]},
            {"Metrica": "Share Non-Shortest (%)", "Valore": share_sp.loc[share_sp["Group"]=="Non-Shortest","Share_%"].values[0]},
            {"Metrica": "TTI mean abs err", "Valore": tti_abs},
            {"Metrica": "TTI mean rel err", "Valore": tti_rel},
            {"Metrica": "U_MAX usato", "Valore": u_max},
        ]
        pd.DataFrame(rows).to_excel(xl, sheet_name="Summary", index=False)

        dfA_enr.to_excel(xl, sheet_name="Assignments_enriched", index=False)
        if share_p is not None:
            share_p.reset_index().rename(columns={"index":"Path_ID"}).to_excel(xl, sheet_name="Shares_by_PathID", index=False)
        share_sp.to_excel(xl, sheet_name="Shares_SP_vs_NSP", index=False)
        if df_tti is not None and not df_tti.empty:
            df_tti.to_excel(xl, sheet_name="TTI_check_samples", index=False)

    return {
        "file": xls_path.name,
        "status": "ok",
        "Weighted_Inconv": inconv_w,
        "Weighted_Extra_Ratio": extra_w,
        "Weighted_FF_Ratio": ffr_w,
        "Share_SP_%": float(share_sp.loc[share_sp["Group"]=="Shortest","Share_%"].values[0]),
        "Share_NSP_%": float(share_sp.loc[share_sp["Group"]=="Non-Shortest","Share_%"].values[0]),
        "TTI_abs_err": tti_abs,
        "TTI_rel_err": tti_rel,
        "U_MAX": u_max
    }

def main():
    in_dir = Path(INPUT_DIR)
    out_root = Path(OUT_DIR)
    out_root.mkdir(parents=True, exist_ok=True)

    files = sorted(in_dir.rglob(FILE_GLOB))
    if not files:
        print(f"⚠️ Nessun file '{FILE_GLOB}' trovato in {in_dir.resolve()}")
        sys.exit(0)

    print(f"🔎 Trovati {len(files)} file da analizzare.")
    results = []
    for i, f in enumerate(files, 1):
        print(f"[{i}/{len(files)}] Analizzo: {f.name}")
        out_base = out_root / f.stem
        res = analyze_one(f, out_base)
        results.append(res)
        if res.get("status") != "ok":
            print(f"   → {res.get('status')}: {res.get('msg','')}")

    # master report
    df_res = pd.DataFrame(results)
    master_xlsx = out_root / "MASTER_report.xlsx"
    with pd.ExcelWriter(master_xlsx, engine="openpyxl") as xl:
        df_res.to_excel(xl, sheet_name="Files_Summary", index=False)

        # una tabella “pulita” solo per gli ok
        cols = ["file","Weighted_Inconv","Weighted_Extra_Ratio","Weighted_FF_Ratio",
                "Share_SP_%","Share_NSP_%","TTI_abs_err","TTI_rel_err","U_MAX"]
        ok = df_res[df_res["status"]=="ok"][cols].sort_values("file")
        ok.to_excel(xl, sheet_name="OK_only", index=False)

    print(f"✅ Finito. Output in: {out_root.resolve()}")
    print(f"📊 Master report: {master_xlsx}")

if __name__ == "__main__":
    main()
