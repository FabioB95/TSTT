import json
import pandas as pd
import os

# === CONFIGURAZIONE ===
TRIPS_TEMPORAL_PATH = "dati/trips_with_paths_temporal_15minuti_1.json"
ARCS_PATH = "dati/arcs_bidirectional.json"
NODES_PATH = "dati/nodes_with_indices.json"

OUTPUT_EXCEL = "./INPUT_DATASETS/dataset_1.xlsx"

os.makedirs(os.path.dirname(OUTPUT_EXCEL), exist_ok=True)

# === 1. Foglio: ARCS ===
with open(ARCS_PATH, "r", encoding="utf-8") as f:
    arcs_raw = json.load(f)

if isinstance(arcs_raw, dict) and "edges" in arcs_raw:
    arcs_data = arcs_raw["edges"]
elif isinstance(arcs_raw, list):
    arcs_data = arcs_raw
else:
    raise ValueError("Formato inatteso di arcs_bidirectional.json")

arcs_list = []
for arc in arcs_data:
    from_node = str(arc["from_node"])
    to_node = str(arc["to_node"])
    capacity = float(arc.get("capacity", 9999))

    distance = float(arc.get("distance", 0.0))
    maxspeed = float(arc.get("maxspeed", 1.0))
    fftt = distance / maxspeed * 60.0 if maxspeed > 0 else 0.0

    arcs_list.append({
        "arc_id": f"{from_node}_{to_node}",
        "from_node": from_node,
        "to_node": to_node,
        "capacity": capacity,
        "fftt": fftt
    })

df_arcs = pd.DataFrame(arcs_list)

# === 2. Foglio: TRIPS ===
with open(TRIPS_TEMPORAL_PATH, "r", encoding="utf-8") as f:
    trips_raw = json.load(f)

if isinstance(trips_raw, dict) and "trips" in trips_raw:
    trips_data = trips_raw["trips"]
elif isinstance(trips_raw, list):
    trips_data = trips_raw
else:
    raise ValueError("Formato inatteso di trips temporal JSON")

trip_rows = []

for trip in trips_data:
    row = {
        "trip_id": trip["ID"],
        "origin": trip["origin"],
        "destination": trip["destination"],
        "demand": trip["demand"],
    }

    paths = trip.get("paths", [])
    for i in range(3):
        path_key = f"path_{i}"
        time_key = f"tempo_{i}"
        dept_key = f"possible_departure_times_{i}"
        pref_key = f"preferenza_{i}"

        if i < len(paths):
            p = paths[i]
            row[path_key] = str(p["arcs"])  # List of arcs as string
            row[time_key] = sum(p.get("base_times", [0]))  # Sum of base times
            row[dept_key] = str(p.get("possible_departure_times", []))  # List of times as string
            row[pref_key] = p.get("preference", "")  # ← CORRECT: READ FROM JSON!
        else:
            row[path_key] = None
            row[time_key] = None
            row[dept_key] = None
            row[pref_key] = None

    trip_rows.append(row)

df_trips = pd.DataFrame(trip_rows)

# === 3. Foglio: NODES ===
with open(NODES_PATH, "r", encoding="utf-8") as f:
    nodes_raw = json.load(f)

if isinstance(nodes_raw, dict) and "nodes" in nodes_raw:
    nodes_data = nodes_raw["nodes"]
else:
    raise ValueError("Formato inatteso di nodes_with_indices.json")

nodes_list = []
for n in nodes_data:
    nodes_list.append({
        "ID": n["ID"],
        "name": n.get("name", ""),
        "lat": n["lat"],
        "lon": n["lon"],
        "population": n.get("population", 0),
        "category": n.get("category", "other"),
        "K_i": n.get("K_i", 0.0),
    })

df_nodes = pd.DataFrame(nodes_list)

# === Scrivi su Excel ===
with pd.ExcelWriter(OUTPUT_EXCEL, engine='openpyxl') as writer:
    df_arcs.to_excel(writer, sheet_name='arcs', index=False)
    df_trips.to_excel(writer, sheet_name='trips', index=False)
    df_nodes.to_excel(writer, sheet_name='nodes', index=False)

print(f"✅ File Excel generato: {OUTPUT_EXCEL}")