from xlsxwriter import Workbook
import pandas as pd
import numpy as np
import re, ast

# === Config ===
INPUT_XLSX  = "dataset_high_traffic_benchmark_fixed_departure_2000.xlsx"  
OUTPUT_XLSX = "Data_HIGH_bench0_2000.xlsx"     
SHEET_ARCS  = "arcs"
SHEET_TRIPS = "trips"
SHEET_NODES = "nodes"
SEED = 42  # per riproducibilità della scelta casuale
rng = np.random.default_rng(SEED)

# === Lettura workbook (3 pagine) ===
book = pd.read_excel(INPUT_XLSX, sheet_name=None)

# Se i fogli non esistono, crea DataFrame vuoti (così non va in errore)
arcs  = book.get(SHEET_ARCS,  pd.DataFrame())
trips = book.get(SHEET_TRIPS, pd.DataFrame())
nodes = book.get(SHEET_NODES, pd.DataFrame())

# === Funzioni utili ===
def parse_times(val):
    """Prova a estrarre una lista di interi da stringhe tipo '[0, 52]', '0,52', '0; 52', ecc."""
    if pd.isna(val):
        return []
    if isinstance(val, (list, tuple, set)):
        return [int(x) for x in val if re.fullmatch(r"-?\d+", str(x).strip())]
    s = str(val).strip()
    # 1) prova a valutare come Python literal (es. '[0, 52]')
    try:
        obj = ast.literal_eval(s)
        if isinstance(obj, (list, tuple, set)):
            return [int(x) for x in obj if re.fullmatch(r"-?\d+", str(x).strip())]
        if isinstance(obj, (int, float)) and float(obj).is_integer():
            return [int(obj)]
    except Exception:
        pass
    # 2) fallback: prendi tutte le cifre presenti
    return [int(n) for n in re.findall(r"-?\d+", s)]

def choose_0_or_52(times):
    """Ritorna 0 o 52 se presenti. Se entrambi, sceglie a caso. Se nessuno dei due, NaN."""
    has0 = 0 in times
    has52 = 52 in times
    if has0 and has52:
        return int(rng.choice([0, 52]))
    elif has52:
        return 52
    elif has0:
        return 0
    else:
        return np.nan

# === Trasforma la pagina 'trips' ===
col = "possible_departure_times_0"
if col in trips.columns:
    parsed = trips[col].apply(parse_times)
    trips["departure_time_0"] = parsed.apply(choose_0_or_52)

    # Se preferisci sovrascrivere la colonna originale (invece di aggiungerne una nuova),
    # scommenta la riga qui sotto:
    trips[col] = trips["departure_time_0"]

# === Scrivi il nuovo Excel con 3 pagine identiche (trips aggiornato) ===
with pd.ExcelWriter(OUTPUT_XLSX, engine="xlsxwriter") as writer:
    arcs.to_excel(writer,  index=False, sheet_name=SHEET_ARCS)
    trips.to_excel(writer, index=False, sheet_name=SHEET_TRIPS)
    nodes.to_excel(writer, index=False, sheet_name=SHEET_NODES)

print(f"Creato: {OUTPUT_XLSX}")
