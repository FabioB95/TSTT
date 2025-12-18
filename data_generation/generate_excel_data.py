import json
import pandas as pd

# === Percorsi dei file ===
TRIPS_TEMPORAL_PATH = "dati/trips_with_paths_temporal_15minuti_10.json"
ARCS_PATH = "dati/arcs_bidirectional.json"
NODES_PATH = "dati/nodes_with_indices.json"

OUTPUT_EXCEL = "output/dataset_10.xlsx"

# Crea la cartella se non esiste
import os
os.makedirs(os.path.dirname(OUTPUT_EXCEL), exist_ok=True)

# === 1. Foglio: ARCS ===
with open(ARCS_PATH, "r") as f:
    arcs_data = json.load(f)

arcs_list = []
for arc in arcs_data:
    # Supponiamo che ogni arco abbia: id, from_node, to_node, capacity, free_flow_time, breakpoints, sigma
    arcs_list.append({
        "ID": arc.get("ID", f"{arc['from_node']}_{arc['to_node']}"),
        "from_node": arc["from_node"],
        "to_node": arc["to_node"],
        "capacity": arc.get("capacity", 9999),
        "fftt": arc.get("free_flow_time", 0),
        "traffic": 0,  # sarà calibrato dopo, per ora 0
        "breakpoints": json.dumps(arc.get("breakpoints", [])),  # come array
        "sigma_values": json.dumps(arc.get("sigma_values", []))  # come array
    })

df_arcs = pd.DataFrame(arcs_list)

# === 2. Foglio: TRIPS ===
with open(TRIPS_TEMPORAL_PATH, "r") as f:
    trips_data = json.load(f)

trip_rows = []

for trip in trips_data:
    row = {
        "trip_id": trip["ID"],
        "origin": trip["origin"],
        "destination": trip["destination"],
        "demand": trip["demand"]
    }

    # Per ogni path (fino a 3, come da K=3)
    for i in range(3):
        path_key = f"path_{i}"
        time_key = f"tempo_{i}"
        dept_key = f"possible_departure_times_{i}"
        pref_key = f"preferenza_{i}"

        if i < len(trip.get("paths", [])):
            p = trip["paths"][i]
            row[path_key] = str(p["arcs"])  # lista di archi
            row[time_key] = sum(p.get("base_times", [0]))
            row[dept_key] = str(p.get("possible_departure_times", []))
            row[pref_key] = 1.0 / (i + 1)  # es. preferenza decresce: 1.0, 0.5, 0.33
        else:
            row[path_key] = None
            row[time_key] = None
            row[dept_key] = None
            row[pref_key] = None

    trip_rows.append(row)

df_trips = pd.DataFrame(trip_rows)

# === 3. Foglio: NODES ===
with open(NODES_PATH, "r") as f:
    nodes_data = json.load(f)["nodes"]

nodes_list = []
for n in nodes_data:
    nodes_list.append({
        "ID": n["ID"],
        "name": n.get("name", ""),
        "lat": n["lat"],
        "lon": n["lon"],
        "population": n.get("population", 0),
        "category": n.get("category", "other"),
        "K_i": n.get("K_i", 0.0)
    })

df_nodes = pd.DataFrame(nodes_list)

# === Scrivi su Excel ===
with pd.ExcelWriter(OUTPUT_EXCEL, engine='openpyxl') as writer:
    df_arcs.to_excel(writer, sheet_name='arcs', index=False)
    df_trips.to_excel(writer, sheet_name='trips', index=False)
    df_nodes.to_excel(writer, sheet_name='nodes', index=False)

print(f"✅ File Excel generato: {OUTPUT_EXCEL}")