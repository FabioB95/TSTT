# dataset_debug.py
import json
import pandas as pd
import math
import numpy as np
import os

print("\n" + "="*60)
print("🔧 CREAZIONE DATASET EXCEL - DEBUG MODE")
print("="*60)

NUM_BREAKPOINTS = 50
UMAX = 4.0  
TTI_MAX = 1.0 + 0.15 * (UMAX ** 4)
print(f"🔧 Breakpoints fino a u_max={UMAX:.3f} (TTI_MAX={TTI_MAX:.2f})")

# === Caricamento dati ===
print("\n📂 Caricamento JSON...")
with open("dati/nodes.json") as f:
    nodes_data = json.load(f)["nodes"]
print(f"✅ Nodi: {len(nodes_data)}")

with open("dati/arcs_bidirectional.json") as f:
    arcs_data = json.load(f)["edges"]
print(f"✅ Archi: {len(arcs_data)}")

with open("dati/traffic_DEF_L.json") as f:
    traffic_data = json.load(f)
print(f"✅ Traffico Z: {len(traffic_data)} archi")

with open("dati/trips_with_paths_temporal_15minuti_50.json") as f:
    trips_data = json.load(f)["trips"]
print(f"✅ Trip: {len(trips_data)}")

# Diagnosi su Z
cap_map = {(str(a["from_node"]), str(a["to_node"])): float(a["capacity"]) for a in arcs_data}
max_u_z = 0.0
for arc_key, d in traffic_data.items():
    i, j = [s.strip() for s in arc_key.split(",")]
    mu_ij = cap_map[(i, j)] / 4.0
    if mu_ij > 0 and d:
        z_max = max(float(v) for v in d.values())
        max_u_z = max(max_u_z, z_max / mu_ij)
if max_u_z > UMAX + 1e-6:
    print(f"⚠️ Z picco = {max_u_z:.2f}x > UMAX={UMAX:.2f}x: valuta clip di Z o u_max più alto.")

# === DataFrame nodi ===
df_nodes = pd.DataFrame(nodes_data)
print(f"📊 Nodi: {df_nodes.shape}")

# === DataFrame archi ===
arcs_list = []
for arc in arcs_data:
    i, j = arc["from_node"], arc["to_node"]
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

# === DataFrame trip ===
trip_records = []
total_paths = 0
total_departures = 0

for idx, trip in enumerate(trips_data):
    demand = trip["demand"]
    paths = trip.get("paths", [])
    num_paths = len(paths)
    total_paths += num_paths

    path_data = {}
    for p_id, p in enumerate(paths):
        arc_ids = [f"{a[0]}_{a[1]}" for a in p["arcs"]]
        base_time = sum(p["base_times"])
        dep_times = p.get("possible_departure_times", [])
        dep_times_clean = [int(float(t)) for t in dep_times if str(t).strip().isdigit()]
        total_departures += len(dep_times_clean)

        if dep_times_clean:
            if max(dep_times_clean) <= 51:
                pref = "giorno1"
            elif min(dep_times_clean) >= 52:
                pref = "giorno2"
            else:
                pref = "entrambi"
        else:
            pref = "nessuno"

        path_data[f"path_{p_id}"] = ",".join(arc_ids)
        path_data[f"tempo_{p_id}"] = round(base_time, 2)
        path_data[f"possible_departure_times_{p_id}"] = ",".join(map(str, dep_times_clean))
        path_data[f"preferenza_{p_id}"] = pref

    origin = paths[0]["arcs"][0][0] if paths else None
    destination = paths[0]["arcs"][-1][1] if paths else None

    trip_records.append({
        "trip_id": idx,
        "origin": origin,
        "destination": destination,
        "demand": demand,
        **path_data
    })

df_trips = pd.DataFrame(trip_records)
print(f"📊 Trip: {len(trip_records)}, Domanda totale: {df_trips['demand'].sum():,.0f}")
print(f"🔗 Path totali: {total_paths}, Finestre temporali: {total_departures}")

# === Salvataggio Excel ===
output_file = "./INPUT_DATASETS/dataset_50_LOW.xlsx"
print(f"\n💾 Salvataggio in {output_file}...")
with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    df_arcs.to_excel(writer, sheet_name="arcs", index=False)
    df_trips.to_excel(writer, sheet_name="trips", index=False)
    df_nodes.to_excel(writer, sheet_name="nodes", index=False)
print(f"✅ Dataset salvato: {output_file}")
print("\n🎉 CREAZIONE DATASET COMPLETATA\n")