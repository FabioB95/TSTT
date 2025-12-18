import json
import random
random.seed(0)

# Carica il file originale
with open("dati/trips_with_paths_temporal.json") as f:
    trips_data = json.load(f)

benchmark_trips = {"trips": []}

for trip in trips_data["trips"]:
    # Seleziona solo il path_0
    selected_path = trip["paths"][0]

    # Scegli un solo departure time casuale tra quelli disponibili
    possible_times = selected_path["possible_departure_times"]
    chosen_time = random.choice(possible_times)

    # Sostituisci possible_departure_times con uno solo
    selected_path["possible_departure_times"] = [chosen_time]

    # Ricrea la struttura del trip
    new_trip = {
        "paths": [selected_path],
        "demand": trip["demand"]
    }

    benchmark_trips["trips"].append(new_trip)

# Salva in un nuovo file
with open("dati/trips_with_paths_temporal_benchmark1.json", "w") as f:
    json.dump(benchmark_trips, f, indent=2)

print("✅ File benchmark salvato in 'dati/trips_with_paths_temporal_benchmark1.json'")
