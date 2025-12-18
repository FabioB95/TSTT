import json
import os
import math
import random
random.seed(0)

# === Configurazioni ===
snapshot_durata = 0.25  # ore per snapshot (15 minuti)
mapping_giorni = {
    1: range(0, 54 ),
    2: range(55, 108),
    (1, 2): range(0, 108)
}

# === Carica fftt da arcs.json ===
with open("dati/arcs_test.json") as f:
    edges = json.load(f)["edges"]

fftt_dict = {(e["from"], e["to"]): e["fftt"] for e in edges}

# === Definizione dei 3 path fissi ===
raw_paths = [
    ["N1", "N2", "N4", "N6", "N7"],
    ["N1", "N2", "N3", "N6", "N7"],
    ["N1", "N2", "N5", "N6", "N7"]
]

# === Funzioni di supporto ===
def calcola_base_times(path):
    return [fftt_dict.get((path[i], path[i+1]), 60) for i in range(len(path)-1)]

def durata_in_snapshot(base_times):
    durata_minuti = sum(base_times)
    durata_ore = durata_minuti / 60
    return math.ceil(durata_ore / snapshot_durata)

def calcola_departure_times(day, durata_snap):
    if isinstance(day, list):
        day_key = tuple(day) if len(day) > 1 else day[0]
    else:
        day_key = day
    snapshot_range = mapping_giorni[day_key]
    ultimi_possibili = max(snapshot_range) - durata_snap
    return [float(t) for t in snapshot_range if t <= ultimi_possibili]

def stima_domanda(base_times, common_departures, giorno):
    durata_media = sum(base_times) / len(base_times)
    rush_bonus = 2 if any(t in range(14, 21) for t in common_departures) else 0 
    giorno_bonus = 3 if giorno == 1 else 1 if giorno == 2 else 2
    rumore = random.randint(0, 3)
    domanda = 1.1*max(1, round(durata_media / 10) + rush_bonus + giorno_bonus + rumore)
    return domanda

# === Genera trips ===
def crea_trips(n, giorno, start_index=0):
    trips = []
    for i in range(n):
        trip_id = f"trip_{start_index + i}"
        trip_paths = []
        all_departure_sets = []

        for j, node_path in enumerate(raw_paths):
            arcs = [[node_path[k], node_path[k+1]] for k in range(len(node_path)-1)]
            base_times = calcola_base_times(node_path)
            durata_snap = durata_in_snapshot(base_times)
            departures = calcola_departure_times(giorno, durata_snap)

            if not departures:
                continue

            all_departure_sets.append(set(departures))

            trip_paths.append({
                "ID": f"{trip_id}_p{j}",
                "arcs": arcs,
                "base_times": base_times,
                "real_times": [],
                "possible_departure_times": departures
            })

        if not trip_paths:
            print(f"⚠️ Trip {trip_id} scartato (nessun path valido)")
            continue

        common_departures = list(set.intersection(*all_departure_sets)) if all_departure_sets else []
        if not common_departures:
            continue

        departure_times = [random.choice(sorted(common_departures))]
        demand_val = stima_domanda(trip_paths[0]["base_times"], common_departures, giorno)

        trips.append({
            "ID": trip_id,
            "origin": "N1",
            "destination": "N7",
            "departure_times": departure_times,
            "demand": demand_val,
            "FP": sum(trip_paths[0]["base_times"]),
            "X": [],
            "paths": trip_paths,
            "schedule": []
        })

    return trips

# === Costruisci tutti i trips ===
trips = []
trips += crea_trips(200, 1, 0)       
trips += crea_trips(300, 2, 200)      
trips += crea_trips(500, [1, 2], 500) 

# === Salva in JSON ===
os.makedirs("dati", exist_ok=True)
with open("dati/trips_test.json", "w") as f:
    json.dump({"trips": trips}, f, indent=4)

print(f"✅ File `dati/trips_test.json` generato con {len(trips)} trips validi.")
domande = [trip["demand"] for trip in trips]
print(f"📊 Domanda media: {sum(domande)/len(domande):.2f}, min: {min(domande)}, max: {max(domande)}")
