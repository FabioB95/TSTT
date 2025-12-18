import json
import random

random.seed(0)

# === Caricamento dati ===
with open("dati/arcs_bidirectional.json") as f:
    arcs_data = json.load(f)["edges"]

with open("dati/trips_with_paths_temporal.json") as f:
    trips_data = json.load(f)["trips"]
#with open("dati/trips_with_paths_temporal_15minuti.json") as f:
#    trips_data = json.load(f)["trips"]

# === Parametri arc: dizionario (da, a) → fftt
FFTT = {}
for a in arcs_data:
    i, j = a["from_node"], a["to_node"]
    try:
        distance = float(a["distance"])
        speed = float(a["maxspeed"])
        if speed > 0:
            fftt = (distance / speed) * 60  # in minuti
            FFTT[(i, j)] = round(fftt, 3)
        else:
            print(f"⚠️ Velocità nulla per l’arco ({i}, {j})")
    except Exception as e:
        print(f"❌ Errore nel calcolo fftt per arco ({i}, {j}): {e}")


# === Costo per trip, path, tau
c_cost = {}
c_cost_FF = {}

beta = 0.1   # random noise
missing_arcs = set()

for c, trip in enumerate(trips_data):
    min_cost = float('inf')
    for p, path_obj in enumerate(trip["paths"]):
        arcs = path_obj["arcs"]
        path_cost = 0
        valid_path = True

        for a in arcs:
            a_tuple = tuple(a)
            if a_tuple in FFTT:
                path_cost += FFTT[a_tuple]
            else:
                missing_arcs.add(a_tuple)
                valid_path = False
                break

        if not valid_path:
            continue

        possible_tau = path_obj.get("possible_departure_times", [])
        if not possible_tau:
            continue

        min_tau = min(possible_tau)

        for tau in possible_tau:
            tau_int = int(tau)
            noise = path_cost * beta * random.uniform(0, 1)
            cost = path_cost + noise
            key = f"{c}_{p}_{tau_int}"
            c_cost[key] = round(cost, 3)

        if path_cost > 0 and path_cost < min_cost:
            min_cost = path_cost


    c_cost_FF[str(c)] = round(min_cost, 3)

if missing_arcs:
    print(f"⚠️ Attenzione: archi mancanti: {missing_arcs}")

# === Salvataggio
with open("dati/c_cost_DEF.json", "w") as f:
    json.dump(c_cost, f, indent=2)

with open("dati/c_cost_FP_DEF.json", "w") as f:
    json.dump(c_cost_FF, f, indent=2)

print("✅ File c_cost_DEF.json e c_cost_FP_DEF.json creati con successo.")
