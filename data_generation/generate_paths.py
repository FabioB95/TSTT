import json
import networkx as nx
import matplotlib.pyplot as plt
from tqdm import tqdm
from itertools import islice
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from model.trip import Trip
from model.path import Path
from model.node import Nodo
from load_data import load_arcs

# === Parametri ===
K = 3
NODES_WITH_INDEX_PATH = 'dati/nodes_with_indices.json'
GRAFO_ARCS_PATH = 'dati/arcs_bidirectional.json'
TRIPS_PATH = 'dati/trips_5000.json'
OUTPUT_PATH = 'dati/trips_with_paths_5000.json'
NODI_PROB_PATH = 'dati/nodi_prob.json'

# === Caricamento grafo ===
def load_nodes_with_index(filepath):
    with open(filepath) as f:
        data = json.load(f)["nodes"]
    return [Nodo(ID=d["ID"], lat=d["lat"], lon=d["lon"], P=0.0, H=0.0, K=d.get("K_i", 0.0), I=0.0) for d in data]

nodes = load_nodes_with_index(NODES_WITH_INDEX_PATH)
arcs = load_arcs(GRAFO_ARCS_PATH)
arcs_dict = {(a.from_node, a.to_node): a.free_flow_time for a in arcs}

G = nx.DiGraph()
for n in nodes:
    G.add_node(n.ID, lat=n.lat, lon=n.lon)
for a in arcs:
    weight = getattr(a, 'distance', a.free_flow_time)
    G.add_edge(a.from_node, a.to_node, weight=weight)

isolati = list(nx.isolates(G))
print(f"[INFO] Nodi isolati: {len(isolati)}")

# === Carica probabilità normalizzate ===
with open(NODI_PROB_PATH, 'r') as f:
    prob_data = json.load(f)

P_dict = {n["ID"]: float(n["origin_prob"]) for n in prob_data}
A_dict = {n["ID"]: float(n["dest_prob"]) for n in prob_data}

# === Carica trips ===
with open(TRIPS_PATH, 'r') as f:
    trip_dicts = json.load(f)

total_trips = len(trip_dicts) 
print(total_trips)

def fix_keys(d, total_trips):
    preference = int(d["preferences"])
    day = int(d["departure_day"])
    base_time = int(d["departure_time"])
    if preference == 0:
        departure_times = [base_time]
    elif preference == 1:
        departure_times = [base_time + 52]
    elif preference == 2:
        departure_times = [base_time, base_time + 52]
    else:
        departure_times = [base_time]

    origin = d["origin"]
    dest = d["destination"]

    #calcolo domanda
    p_gen = P_dict.get(origin, 0.0)*100
    p_attr = A_dict.get(dest, 0.0)*100
    demand = max(1, round(p_gen * p_attr * total_trips))  

    return Trip(
        ID=d["ID"],
        origin=origin,
        destination=dest,
        departure_times=departure_times,
        demand=demand
    )

trips = []
for d in trip_dicts:
    try:
        trips.append(fix_keys(d, total_trips))
    except Exception as e:
        print(f"[ERRORE Trip] ID={d.get('id', '???')}: {e}")
print(f"[INFO] Totale trips caricati: {len(trips)}")

# === Generazione paths ===
for trip in tqdm(trips, desc="Generazione paths"):
    origin, destination = trip.origin, trip.destination
    if not G.has_node(origin) or not G.has_node(destination):
        continue
    try:
        simple_paths = islice(nx.shortest_simple_paths(G, origin, destination, weight='weight'), K)
        for i, path_nodes in enumerate(simple_paths):
            arcs_path = [(path_nodes[j], path_nodes[j+1]) for j in range(len(path_nodes)-1)]
            base_times = []
            for arc in arcs_path:
                t = arcs_dict.get(arc, 10.0)
                if t <= 0:
                    t = 10.0
                base_times.append(round(t))  # Arrotonda a minuti

            path_obj = Path(ID=f"{trip.ID}_p{i}", arcs=arcs_path)
            path_obj.base_times = base_times
            trip.paths.append(path_obj)

        # Calcolo FP
        if trip.paths:
            total_times = [sum(p.base_times) for p in trip.paths]
            trip.FP = round(min(total_times)) if total_times else 1
        else:
            trip.FP = 1

    except Exception as e:
        trip.FP = 1
        print(f"[ERRORE Path] Trip {trip.ID}: {e}")

# === Salvataggio JSON ===
with open(OUTPUT_PATH, 'w') as f:
    json.dump([t.to_dict() for t in trips], f, indent=2)
print(f"✅ Salvati {len(trips)} trips in {OUTPUT_PATH}")
