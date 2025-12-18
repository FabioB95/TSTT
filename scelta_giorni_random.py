# pip install pandas xlsxwriter
from xlsxwriter import Workbook  # opzionale: non strettamente necessario
import pandas as pd
import numpy as np
import re, ast

# === Config ===
INPUT_XLSX  = "dataset_null_benchmark_balanced_random_departure_2000.xlsx"
OUTPUT_XLSX = "Data_NOTRAF_bench_random_2000.xlsx"
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
    """
    Estrae una lista di interi da valori tipo:
    - '80'
    - '38,70'  / '10,75'  / '24,100'
    - '[2, 88]'
    - '2;88'   / '2 88'
    """
    if pd.isna(val):
        return []
    if isinstance(val, (list, tuple, set)):
        return [int(x) for x in val if re.fullmatch(r"-?\d+", str(x).strip())]

    s = str(val).strip()

    # 1) Prova come literal Python (gestisce '[2, 88]' ecc.)
    try:
        obj = ast.literal_eval(s)
        if isinstance(obj, (list, tuple, set)):
            return [int(x) for x in obj if re.fullmatch(r"-?\d+", str(x).strip())]
        if isinstance(obj, (int, float)) and float(obj).is_integer():
            return [int(obj)]
    except Exception:
        pass

    # 2) Fallback: prendi tutte le cifre (gestisce '2,88', '24;100', '20 60')
    return [int(n) for n in re.findall(r"-?\d+", s)]

def choose_one(times):
    """
    - Nessun numero -> NaN
    - Uno solo -> quello
    - Due o più -> sceglie *a caso* uno tra i presenti
    """
    if not times:
        return np.nan
    if len(times) == 1:
        return int(times[0])
    return int(rng.choice(times))

# === Trasforma la pagina 'trips' ===
col = "possible_departure_times_0"
if col in trips.columns:
    parsed = trips[col].apply(parse_times)
    trips["departure_time_0"] = parsed.apply(choose_one)

    # Se vuoi sostituire la colonna originale con il valore scelto:
    trips[col] = trips["departure_time_0"]
    # (in alternativa, lascia la riga sopra commentata per mantenere anche l'originale)

# === Scrivi il nuovo Excel con 3 pagine (trips aggiornato) ===
with pd.ExcelWriter(OUTPUT_XLSX, engine="xlsxwriter") as writer:
    arcs.to_excel(writer,  index=False, sheet_name=SHEET_ARCS)
    trips.to_excel(writer, index=False, sheet_name=SHEET_TRIPS)
    nodes.to_excel(writer, index=False, sheet_name=SHEET_NODES)

print(f"Creato: {OUTPUT_XLSX}")
