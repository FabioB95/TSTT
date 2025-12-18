import json
from node import Nodo
from arc import Arc
from trip import Trip
from path import Path
from traffic import Traffic

def load_json(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)

def debug_print(title, data):
    print(f"\n{'='*20} {title} {'='*20}")
    for k, v in data.items():
        print(f"{k}: {v}")
    print('='*60)

def load_nodes(file_path):
    node_data = load_json(file_path)["nodes"]
    return {d["ID"]: Nodo.from_dict(d) for d in node_data}

def load_arcs(file_path):
    arc_data = load_json(file_path)["edges"]
    return { (d["from_node"], d["to_node"]): Arc.from_dict(d) for d in arc_data }

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
            demand=d["demand"],
            possible_departure_times=d["possible_departure_times"]
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

def main():
    nodes = load_nodes("dati/nodes.json")
    debug_print("NODI", nodes)

    arcs = load_arcs("dati/arcs.json")
    debug_print("ARCHI", arcs)

    trips, paths = load_trips_and_paths("dati/trips_with_paths_temporal.json")
    debug_print("TRIPS", trips)
    debug_print("PATHS", paths)

    traffic = load_traffic("dati/traffic_DEF.json")
    debug_print("TRAFFIC", traffic)

if __name__ == "__main__":
    main()
