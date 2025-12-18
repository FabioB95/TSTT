import json
from datetime import timedelta

# === Percorsi ai file ===
INPUT_PATH = "dati/trips_with_paths.json"
OUTPUT_PATH = "dati/trips_with_paths_temporal.json"

# === Costante: orario limite arrivo (19:00 = 1140 minuti)
MAX_ARRIVAL_MINUTES = 1140  # 19:00
START_DAY_MINUTES = 360     # 6:00

# === Caricamento trips con paths
with open(INPUT_PATH, "r") as f:
    trips = json.load(f)

# === Nuova lista per output
updated_trips = []

for trip in trips:
    updated_paths = []

    
    # === VERSIONE SEMPLIFICATA: considera solo giorno 1 (0) o giorno 2 (27)
    """""
    original_slots = trip.get("departure_times", [])
    starting_slots = []
    for s in original_slots:
        if s <= 25:
            if 0 not in starting_slots:
                starting_slots.append(0)
        else:
            if 26 not in starting_slots:
                starting_slots.append(27)
    """""
    # === VERSIONE PREDEFINITA: con slot decisi - simulazione app
    starting_slots = trip.get("departure_times", [])
    for path in trip["paths"]:
        base_times = path.get("base_times", [])
        if not base_times or sum(base_times) <= 0:
            continue

        travel_time = round(sum(base_times))  # in minuti
        if travel_time >= (MAX_ARRIVAL_MINUTES - START_DAY_MINUTES):
            continue  # percorso troppo lungo per qualsiasi orario valido

        possible_departures = []

        for day_slot in starting_slots:
            if day_slot <= 25:
                # Giorno 1
                day_index = 0
                slot_in_day = day_slot
            else:
                # Giorno 2
                day_index = 1
                slot_in_day = day_slot - 26

            base_day_minute = 780 * day_index  # 0 per giorno 1, 780 per giorno 2 --> ovvero 6AM giorno 2 --> prendo le ore effettive che compraimo con gli slot 
            day_start_minute = base_day_minute + START_DAY_MINUTES
            day_end_minute = base_day_minute + MAX_ARRIVAL_MINUTES
            

            latest_departure_minute = day_end_minute - travel_time

            # Genera partenze ogni 30 minuti
            for dep_minute in range(day_start_minute, latest_departure_minute + 1, 30):
                
                possible_departures.append(dep_minute)
            possible_departures_slot = [t / 30-12 for t in possible_departures] #--> li metto in slot di 30 minuti
            print(possible_departures)
            print(possible_departures_slot)

        path["possible_departure_times"] = possible_departures_slot
        #path["possible_departure_times"] = possible_departures

        # stampa HH:MM 
        #print(f"{path['ID']}: {[str(timedelta(minutes=t))[:-3] for t in possible_departures]}")

        updated_paths.append(path)

    if updated_paths:
        trip["paths"] = updated_paths
        updated_trips.append(trip)

# === Scrittura file aggiornato
with open(OUTPUT_PATH, "w") as f:
    json.dump(updated_trips, f, indent=2)

print(f"✅ File generato con possibili orari di partenza: {OUTPUT_PATH}")
