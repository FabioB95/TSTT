import numpy as np
import json

# Carica il file degli archi
with open("dati/arcs_bidirectional.json") as f:
    arcs_data = json.load(f)["edges"]

# Numero di segmenti per la linearizzazione
num_breakpoints = 20
linearization = {}

for arc in arcs_data:
    i, j = arc["from_node"], arc["to_node"]
    try:
        distance_km = float(arc["distance"])
        speed_kmh = float(arc["maxspeed"])
        capacity = float(arc["capacity"])

        if speed_kmh <= 0 or capacity <= 0:
            print(f"⚠️ Arco ({i},{j}) ha dati non validi: velocità={speed_kmh}, capacità={capacity}")
            continue

        fftt = (distance_km / speed_kmh) * 60  # in minuti
        breakpoints = np.linspace(0, 4 * capacity, num_breakpoints + 1)
        tti_values = 1 + 0.15 * (breakpoints / capacity) ** 4
        tti_fftt = tti_values * fftt
        slopes = np.diff(tti_fftt) / np.diff(breakpoints)

        linearization[f"{i}_{j}"] = {
            "capacity": capacity,
            "fftt": round(fftt, 3),
            "breakpoints": breakpoints.tolist(),
            "tti_values": tti_values.tolist(),
            "tti_fftt_values": tti_fftt.tolist(),
            "slopes": slopes.tolist()
        }

    except Exception as e:
        print(f"❌ Errore nel processare l’arco ({i},{j}): {e}")
        continue

# Salvataggio
with open("dati/linearization_DEF.json", "w") as f:
    json.dump(linearization, f, indent=4)

print("✅ File linearization_DEF.json creato con successo.")
