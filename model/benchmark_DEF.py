# generate_benchmark_fixed_departure.py
import json
import pandas as pd
import numpy as np
import os

print("\n" + "="*60)
print("🔧 CREAZIONE DATASET BENCHMARK FIXED DEPARTURE - DEBUG MODE")
print("="*60)

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

with open("dati/traffic_DEF_H.json") as f:
    traffic_data = json.load(f)
print(f"✅ Traffico Z: {len(traffic_data)} archi")

trips_file = "dati/trips_with_paths_temporal_15minuti_1.json"
if not os.path.exists(trips_file):
    raise FileNotFoundError(f"❌ File {trips_file} non trovato")

with open(trips_file, "r") as f:
    trips_data = json.load(f)["trips"]
print(f"✅ Trip: {len(trips_data)}")

# === DataFrame nodi ===
df_nodes = pd.DataFrame(nodes_data)
print(f"📊 Nodi: {df_nodes.shape}")

# === DataFrame archi (IDENTICO all'originale) ===
arcs_list = []
for arc in arcs_data:
    i, j = str(arc["from_node"]), str(arc["to_node"])
    try:
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
        print(f"❌ Errore arco {i}_{j}: {e}")

df_arcs = pd.DataFrame(arcs_list)
print(f"📊 Archi: {df_arcs.shape}")
print(f"📈 Capacità media (oraria): {df_arcs['capacity'].mean():.1f}")
print(f"📈 FFTT medio: {df_arcs['fftt'].mean():.1f} min")
print(f"📈 Utilizzo max nei breakpoint: {UMAX}x")

# === DataFrame trip (MODIFICATO: partenze fisse) ===
trip_records = []
weights = []

print("🔁 Preparazione trip con partenze fisse...")
for idx, trip in enumerate(trips_data):
    paths = trip.get("paths", [])
    if not paths:
        continue

    # ✅ Usa solo il path_0 (shortest path)
    best_path = paths[0]  # path_0
    origin = best_path["arcs"][0][0]
    dest = best_path["arcs"][-1][1]

    # Peso per distribuzione domanda
    with open("dati/nodi_prob.json", "r") as f:
        prob_data = json.load(f)
    P_dict = {n["ID"]: float(n["origin_prob"]) for n in prob_data}
    A_dict = {n["ID"]: float(n["dest_prob"]) for n in prob_data}

    p_gen = P_dict.get(str(origin), 0.0001)
    p_attr = A_dict.get(str(dest), 0.0001)
    random_factor = np.random.uniform(0.8, 1.2)
    weight = p_gen * p_attr * random_factor
    weights.append(weight)

    # Info percorso
    arc_ids = [f"{a[0]}_{a[1]}" for a in best_path["arcs"]]
    path_str = ",".join(arc_ids)
    base_time = sum(best_path.get("base_times", []))

    # ✅ Determina partenze fisse
    dep_times_raw = best_path.get("possible_departure_times", [])
    dep_clean = [int(float(t)) for t in dep_times_raw if str(t).strip().replace(".", "").isdigit()]

    if not dep_clean:
        preferenza = "nessuno"
        possible_departure_times = []
    else:
        mn, mx = min(dep_clean), max(dep_clean)
        if mx <= 51:
            preferenza = "giorno1"
            possible_departure_times = [0]  # ✅ Partenza fissa a 0
        elif mn >= 52:
            preferenza = "giorno2"
            possible_departure_times = [52]  # ✅ Partenza fissa a 52
        else:
            preferenza = "entrambi"
            possible_departure_times = [0, 52]  # ✅ Entrambe le partenze

    trip_records.append({
        "trip_id": idx,
        "origin": origin,
        "destination": dest,
        "demand": 0,  # Verrà settato dopo
        "path_0": path_str,
        "tempo_0": round(base_time, 2),
        "possible_departure_times_0": ",".join(map(str, possible_departure_times)),
        "preferenza_0": preferenza
    })

# === Distribuzione domanda a 38,773 ===
print("🎯 Distribuzione domanda a 38,773...")
total_weight = sum(weights)
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
print(f"📊 Trip: {len(df_trips)}, Domanda totale: {total_demand:,}")
assert total_demand == TOTAL_DEMAND, "❌ Domanda totale non corrisponde!"

# === Salvataggio Excel  ===
output_file = "dataset_benchmark_0_1_HIGH.xlsx"
print(f"\n💾 Salvataggio in {output_file}...")
with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    df_arcs.to_excel(writer, sheet_name="arcs", index=False)
    df_trips.to_excel(writer, sheet_name="trips", index=False)
    df_nodes.to_excel(writer, sheet_name="nodes", index=False)
print(f"✅ Dataset salvato: {output_file}")

print("\n🎉 CREAZIONE BENCHMARK COMPLETATA\n")