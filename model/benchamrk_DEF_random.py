# generate_benchmark_balanced_random_departure.py
import json
import pandas as pd
import numpy as np
import os

print("\n" + "="*60)
print("🔧 CREAZIONE BENCHMARK BALANCED RANDOM DEPARTURE")
print("="*60)

# === PARAMETRI ===
NUM_BREAKPOINTS = 50
UMAX = 4.0  
TTI_MAX = 1.0 + 0.15 * (UMAX ** 4)
TOTAL_DEMAND = 100
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

print(f"🔧 Breakpoints fino a u_max={UMAX:.3f} (TTI_MAX={TTI_MAX:.2f})")
print(f"🔧 Domanda totale target: {TOTAL_DEMAND:,}")

# === Caricamento dati ===
print("\n📂 Caricamento JSON...")
with open("dati/nodes.json") as f:
    nodes_data = json.load(f)["nodes"]
print(f"✅ Nodi: {len(nodes_data)}")

with open("dati/arcs_bidirectional.json") as f:
    arcs_data = json.load(f)["edges"]
print(f"✅ Archi: {len(arcs_data)}")

with open("dati/traffic_DEF_null.json") as f:
    traffic_data = json.load(f)
print(f"✅ Traffico Z: {len(traffic_data)} archi")

trips_file = "dati/trips_with_paths_temporal_15minuti_1.json"
if not os.path.exists(trips_file):
    raise FileNotFoundError(f"❌ File {trips_file} non trovato")

with open(trips_file, "r") as f:
    trips_data = json.load(f)["trips"]
print(f"✅ Trip: {len(trips_data)}")

# === Diagnosi su Z ===
cap_map = {(str(a["from_node"]), str(a["to_node"])): float(a["capacity"]) for a in arcs_data}
max_u_z = 0.0
for arc_key, d in traffic_data.items():
    try:
        i, j = [s.strip() for s in arc_key.split(",")]
        mu_ij = cap_map.get((i, j), 0.0) / 4.0
        if mu_ij > 0 and d:
            z_max = max(float(v) for v in d.values())
            max_u_z = max(max_u_z, z_max / mu_ij)
    except:
        continue
if max_u_z > UMAX + 1e-6:
    print(f"⚠️ Z picco = {max_u_z:.2f}x > UMAX={UMAX:.2f}x: valuta clip di Z o u_max più alto.")

# === DataFrame nodi ===
df_nodes = pd.DataFrame(nodes_data)
print(f"📊 Nodi: {df_nodes.shape}")

# === DataFrame archi (IDENTICO all'originale) ===
arcs_list = []
for idx, arc in enumerate(arcs_data):
    try:
        i, j = str(arc["from_node"]), str(arc["to_node"])
        distance = float(arc["distance"])
        speed = float(arc["maxspeed"])
        capacity = float(arc["capacity"])
        raw_fftt = (distance / speed) * 60
        fftt = max(0.05, raw_fftt)
        mu_15 = capacity / 4.0
        x_vals = np.linspace(0, UMAX * mu_15, NUM_BREAKPOINTS + 1)
        sigma_vals = (fftt * (x_vals + 0.03 * (x_vals**5) / ((mu_15**4) + 1e-12))).round(3)

        key = f"{i},{j}"
        arc_traffic = traffic_data.get(key, {})
        max_traffic = max([float(v) for v in arc_traffic.values()] or [0])

        arcs_list.append({
            "arc_id": f"{i}_{j}",
            "from_node": i,
            "to_node": j,
            "capacity": capacity,
            "fftt": round(fftt, 3),
            "max_exogenous": round(max_traffic, 2),
            "breakpoints": x_vals.tolist(),
            "sigma_values": sigma_vals.tolist()
        })
        
    except Exception as e:
        print(f"⚠️ Errore arco {idx} ({arc.get('from_node', '?')}_{arc.get('to_node', '?')}): {e}")
        continue

df_arcs = pd.DataFrame(arcs_list)
print(f"📊 Archi: {df_arcs.shape}")

if len(df_arcs) > 0:
    print(f"📈 Capacità media (oraria): {df_arcs['capacity'].mean():.1f}")
    print(f"📈 FFTT medio: {df_arcs['fftt'].mean():.1f} min")
    print(f"📈 Utilizzo max nei breakpoint: {UMAX}x")
else:
    print("❌ ERRORE: Nessun arco processato correttamente!")
    exit(1)

# === DataFrame trip (MODIFICATO: scelta bilanciata random) ===
trip_records = []
weights = []

print("🔁 Preparazione trip con scelta bilanciata random...")
for idx, trip in enumerate(trips_data):
    paths = trip.get("paths", [])
    if not paths:
        continue

    # ✅ Usa solo il path_0 (primo percorso)
    best_path = paths[0]
    origin = best_path["arcs"][0][0]
    dest = best_path["arcs"][-1][1]

    # Peso per distribuzione domanda
    try:
        with open("dati/nodi_prob.json", "r") as f:
            prob_data = json.load(f)
        P_dict = {str(n["ID"]): float(n["origin_prob"]) for n in prob_data}
        A_dict = {str(n["ID"]): float(n["dest_prob"]) for n in prob_data}

        p_gen = P_dict.get(str(origin), 0.0001)
        p_attr = A_dict.get(str(dest), 0.0001)
        random_factor = np.random.uniform(0.8, 1.2)
        weight = p_gen * p_attr * random_factor
        weights.append(weight)
    except:
        weight = 1.0
        weights.append(weight)

    # Info percorso (solo path_0)
    arc_ids = [f"{a[0]}_{a[1]}" for a in best_path["arcs"]]
    path_str = ",".join(arc_ids)
    base_time = sum(best_path.get("base_times", []))

    # ✅ Determina partenze disponibili e separa per giorni
    dep_times_raw = best_path.get("possible_departure_times", [])
    dep_clean = [int(float(t)) for t in dep_times_raw if str(t).strip().replace(".", "").isdigit()]

    if not dep_clean:
        preferenza = "nessuno"
        final_departure_times = []  # ✅ Nessuna partenza possibile
    else:
        # Separa partenze per giorni
        giorno1_times = [t for t in dep_clean if t <= 51]
        giorno2_times = [t for t in dep_clean if t >= 52]
        
        # Determina preferenza
        if len(giorno2_times) == 0:
            preferenza = "giorno1"
        elif len(giorno1_times) == 0:
            preferenza = "giorno2"
        else:
            preferenza = "entrambi"
        
        # ✅ Scegli random bilanciata:
        selected_departures = []
        
        if giorno1_times:
            selected_departures.append(int(np.random.choice(giorno1_times)))
        
        if giorno2_times:
            selected_departures.append(int(np.random.choice(giorno2_times)))
        
        final_departure_times = selected_departures  # ✅ Solo le partenze scelte!

    trip_records.append({
        "trip_id": idx,
        "origin": origin,
        "destination": dest,
        "demand": 0,  # Verrà settato dopo
        "path_0": path_str,
        "tempo_0": round(base_time, 2),
        "possible_departure_times_0": ",".join(map(str, final_departure_times)),  # ✅ Partenze scelte!
        "preferenza_0": preferenza
    })

print(f"📊 Trip processati: {len(trip_records)}")

# === Distribuzione domanda a 14,800,953 ===
print("🎯 Distribuzione domanda a 14,800,953...")
if not weights:
    print("❌ ERRORE: Nessun peso calcolato!")
    exit(1)

total_weight = sum(weights)
if total_weight <= 0:
    print("❌ ERRORE: Somma pesi non valida!")
    exit(1)

demands = [max(1, int(round((w / total_weight) * TOTAL_DEMAND))) for w in weights]

# Correggi il totale
remaining = TOTAL_DEMAND - sum(demands)
indices = list(range(len(demands)))
np.random.shuffle(indices)

for i in indices:
    if remaining == 0:
        break
    if remaining > 0:
        demands[i] += 1
        remaining -= 1
    elif remaining < 0 and demands[i] > 1:
        demands[i] -= 1
        remaining += 1

# Assegna domande
for record, demand in zip(trip_records, demands):
    record["demand"] = demand

df_trips = pd.DataFrame(trip_records)
total_demand = df_trips["demand"].sum()
print(f"📊 Trip finali: {len(df_trips)}, Domanda totale: {total_demand:,}")

if total_demand != TOTAL_DEMAND:
    print(f"⚠️ Attenzione: domanda totale {total_demand:,} ≠ target {TOTAL_DEMAND:,}")
    # Correzione finale
    diff = TOTAL_DEMAND - total_demand
    if len(df_trips) > 0:
        df_trips.iloc[0, df_trips.columns.get_loc("demand")] += diff
        print(f"🔧 Corretto: aggiunto {diff} al primo trip")

# === Salvataggio Excel (IDENTICO alla struttura originale) ===
output_file = "dataset_random_1_NULL.xlsx"
print(f"\n💾 Salvataggio in {output_file}...")
try:
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        df_arcs.to_excel(writer, sheet_name="arcs", index=False)
        df_trips.to_excel(writer, sheet_name="trips", index=False)
        df_nodes.to_excel(writer, sheet_name="nodes", index=False)
    print(f"✅ Dataset salvato: {output_file}")
except Exception as e:
    print(f"❌ Errore salvataggio: {e}")

print("\n🎉 CREAZIONE BENCHMARK BALANCED RANDOM DEPARTURE COMPLETATA\n")