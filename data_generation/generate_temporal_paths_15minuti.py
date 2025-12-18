import json
import os

# === Debug info ===
print("Current working directory:", os.getcwd())
if os.path.exists("dati"):
    print("Files in 'dati' directory:", os.listdir("dati"))
else:
    print("❌ Directory 'dati' not found!")

# === Percorsi ai file ===
INPUT_PATH = "dati/trips_with_paths_15minuti_1.json"
OUTPUT_PATH = "dati/trips_with_paths_temporal_15minuti_1.json"

# === Verifica esistenza file ===
if not os.path.exists(INPUT_PATH):
    print(f"❌ File non trovato: {INPUT_PATH}")
    print("Creating a sample file for testing...")
    
    # Create sample data
    sample_data = [
        {
            "departure_times": [10, 60],
            "paths": [
                {
                    "base_times": [5, 10, 15]
                }
            ]
        }
    ]
    
    os.makedirs("dati", exist_ok=True)
    with open(INPUT_PATH, "w") as f:
        json.dump(sample_data, f, indent=2)
    print("✅ Sample file created!")

# === Costanti temporali ===
START_DAY_MINUTES = 360     # 6:00
END_DAY_MINUTES = 1140      # 19:00
SLOT_DURATION = 15          # ogni 15 minuti
SLOTS_PER_DAY = (END_DAY_MINUTES - START_DAY_MINUTES) // SLOT_DURATION  # 52 slot al giorno

# === Caricamento trips ===
with open(INPUT_PATH, "r") as f:
    trips = json.load(f)

updated_trips = []

for trip in trips:
    updated_paths = []
    starting_slots = trip.get("departure_times", [])

    for path in trip.get("paths", []):
        base_times = path.get("base_times", [])
        if not base_times or sum(base_times) <= 0:
            continue

        travel_time = round(sum(base_times))  # in minuti

        valid_snapshots = []

        for day_slot in starting_slots:
            if day_slot <= 54:
                day_index = 0  # Giorno 1
            else:
                day_index = 1  # Giorno 2

            base_day_minute = day_index * 780  # 0 o 780
            day_start_minute = base_day_minute + START_DAY_MINUTES
            latest_departure_minute = base_day_minute + END_DAY_MINUTES - travel_time

            # Genera partenze ogni 15 minuti
            for dep_minute in range(day_start_minute, latest_departure_minute + 1, SLOT_DURATION):
                snapshot = ((dep_minute - base_day_minute - START_DAY_MINUTES) // SLOT_DURATION) + (day_index * SLOTS_PER_DAY)
                if 0 <= snapshot < 2 * SLOTS_PER_DAY:  # 0 <= snapshot <= 103
                    valid_snapshots.append(snapshot)

        path["possible_departure_times"] = valid_snapshots
        updated_paths.append(path)

    if updated_paths:
        trip["paths"] = updated_paths
        updated_trips.append(trip)

# === Salva su file con wrapper "trips" ===
output_data = {
    "trips": updated_trips
}

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

with open(OUTPUT_PATH, "w") as f:
    json.dump(output_data, f, indent=2)

print(f"✅ File aggiornato generato in: {OUTPUT_PATH}")