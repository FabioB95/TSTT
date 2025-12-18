import json
import random

random.seed(0)

# === Caricamento dati ===
with open("dati/arcs_test.json") as f:
    arcs_data = json.load(f)["edges"]

with open("dati/trips_test.json") as f:
    trips_data = json.load(f)["trips"]

# === Parametri arc: dizionario (da, a) → fftt
FFTT = {(a["from"], a["to"]): a["fftt"] for a in arcs_data}

# === Costo per trip, path, tau
c_cost = {}
c_cost_FF ={}

beta = 0.1   

missing_arcs = set()  

for c, trip in enumerate(trips_data):
    min_cost = 1000000
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
            continue  # salta path senza possibili partenze

        min_tau = min(possible_tau)

        for tau in possible_tau:
            tau_int = int(tau)
            random_noise =path_cost * beta * random.uniform(0, 1)

           
            cost = path_cost + random_noise
            key = f"{c}_{p}_{tau_int}"
            c_cost[key] = round(cost, 3)

        if path_cost < min_cost:
            min_cost = path_cost
    cost = min_cost 
    key = f"{c}"
    c_cost_FF[key] = round(cost, 3)




# vediamo se ci sono archi mancanti
if missing_arcs:
    print(f"⚠️ Attenzione: archi non trovati in FFTT: {missing_arcs}")


# === Salvataggio del dizionario
with open("dati/c_cost.json", "w") as f:
    json.dump(c_cost, f, indent=2)

with open("dati/c_cost_FP.json", "w") as f:
    json.dump(c_cost_FF, f, indent=2)

print(f"✅ File c_cost.json creato con successo ({len(c_cost)} combinazioni).")
print(f"✅ File c_cost_FP.json creato con successo ({len(c_cost_FF)} combinazioni).")
