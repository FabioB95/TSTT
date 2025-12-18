import pickle
import json
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'model')))

from node import Nodo
from arc import Arc
from trip import Trip
from path import Path
from traffic import Traffic



def load_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def load_nodes(file_path):
    return {d["ID"]: Nodo.from_dict(d) for d in load_json(file_path)["nodes"]}

def load_arcs(file_path):
    return {(d["from_node"], d["to_node"]): Arc.from_dict(d) for d in load_json(file_path)["edges"]}

def load_trips_and_paths(file_path):
    data = load_json(file_path)
    trips = {}
    paths = {}
    for d in data:
        trip = Trip(
            ID=d["ID"],
            origin=d["origin"],
            destination=d["destination"],
            departure_times=d["departure_times"],
            demand=d["demand"]
        )
        for p in d["paths"]:
            path = Path.from_dict(p)
            trip.paths.append(path)
            paths[path.ID] = path
        trips[trip.ID] = trip
    return trips, paths

def load_traffic(file_path):
    raw = load_json(file_path)
    traffic_objects = {}
    for arc_str, time_dict in raw.items():
        start, end = arc_str.split(',')
        traffic = Traffic(start, end)
        for t_str, tti in time_dict.items():
            traffic.add_entry(t_str, tti)
        traffic_objects[(start, end)] = traffic
    return traffic_objects

def save_pickle(obj, name):
    with open(f"dati/{name}.pkl", "wb") as f:
        pickle.dump(obj, f)
    print(f"✅ Salvato: dati/{name}.pkl")

def main():
    nodes = load_nodes("dati/nodes.json")
    arcs = load_arcs("dati/arcs.json")
    trips, paths = load_trips_and_paths("dati/trips_with_paths_temporal.json")
    traffic = load_traffic("dati/traffic_DEF.json")

    save_pickle(nodes, "nodes")
    save_pickle(arcs, "arcs")
    save_pickle(trips, "trips")
    save_pickle(paths, "paths")
    save_pickle(traffic, "traffic")

if __name__ == "__main__":
    main()
