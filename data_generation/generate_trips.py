import json
import random
random.seed(0)

# Load the probabilities
with open("dati/nodi_prob.json", "r") as f:
    nodes_prob = json.load(f)

# Create cumulative distributions
origins = [(n["ID"], n["origin_prob"]) for n in nodes_prob if n["origin_prob"] > 0]
destinations = [(n["ID"], n["dest_prob"]) for n in nodes_prob if n["dest_prob"] > 0]

def weighted_choice(items):
    """Sceglie un item in base alla sua probabilità"""
    total = sum(w for _, w in items)
    r = random.uniform(0, total)
    upto = 0
    for item, weight in items:
        if upto + weight >= r:
            return item
        upto += weight
    return items[-1][0]  # fallback

# Genera le richieste
NUM_TRIPS = 1
trips = []
for i in range(NUM_TRIPS):
    origin = weighted_choice(origins)
    dest = weighted_choice(destinations)
    while dest == origin:
        dest = weighted_choice(destinations)

    # Departure time e day
    departure_time = random.randint(0, 104) 
    if departure_time <= 52:
        day = 1
        real_departure_time = departure_time  # tempo invariato
    else:
        day = 2
        real_departure_time = departure_time -52   #  corrisponde a 0 del secondo giorno

    # Preferences
    preference = random.randint(0, 2)

    trip = {
        "ID": f"trip_{i+1}",
        "origin": origin,
        "destination": dest,
        "departure_day": day,
        "departure_time": real_departure_time,
        "preferences": preference
    }
    trips.append(trip)

# Salva
with open("dati/trips_1.json", "w") as f:
    json.dump(trips, f, indent=4)

print("✅ Richieste generate in dati/trips_10.json")
