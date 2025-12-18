import numpy as np
import json

# Carica il file arcs.json
with open("dati/arcs_test.json") as f:
    arcs_data = json.load(f)["edges"]

# Numero di segmenti
num_breakpoints = 20

# Nuovo dizionario
linearization = {}

# Funzione TTI
for arc in arcs_data:
    arc_id = (arc["from"], arc["to"])
    capacity = arc["capacity"]
    fftt = arc["fftt"]

    breakpoints = np.linspace(0, 4*capacity, num_breakpoints + 1)
    
    
    tti_values = 1 + 0.15 * (breakpoints / capacity) ** 4

    linearization[f"{arc_id[0]}_{arc_id[1]}"] = {
        "capacity": capacity,
        "fftt": fftt,
        "breakpoints": breakpoints.tolist(),
        "tti_values": tti_values.tolist()
    }

# Salvataggio
with open("dati/linearization_test.json", "w") as f:
    json.dump(linearization, f, indent=4)

print("✅ File linearization_test.json aggiornato con funzione TTI.")


import numpy as np
import json

# Carica il file
with open("dati/arcs_bidirectional.json") as f:
    arcs_data = json.load(f)["edges"]

# Numero di segmenti
num_breakpoints = 20
linearization = {}

for arc in arcs_data:
    arc_id = (arc["from_node"], arc["to_node"])

    try:
        distance_km = float(arc["distance"])
        speed_kmh = float(arc["maxspeed"])
        capacity = float(arc["capacity"])

        # Calcolo fftt solo se distanza e velocità sono > 0
        if speed_kmh <= 0 or capacity <= 0:
            print(f"⚠️ Arco {arc_id} ha dati non validi (speed={speed_kmh}, capacity={capacity}), salto.")
            continue

        fftt = (distance_km / speed_kmh) * 60

        breakpoints = np.linspace(0, 4 * capacity, num_breakpoints + 1)
        tti_values = 1 + 0.15 * (breakpoints / capacity) ** 4
        tti_fftt = tti_values * fftt
        slopes = np.diff(tti_fftt) / np.diff(breakpoints)

        linearization[f"{arc_id[0]}_{arc_id[1]}"] = {
            "capacity": capacity,
            "fftt": round(fftt, 3),
            "breakpoints": breakpoints.tolist(),
            "tti_values": tti_values.tolist(),
            "tti_fftt_values": tti_fftt.tolist(),
            "slopes": slopes.tolist()
        }

    except Exception as e:
        print(f"❌ Errore nel processare arco {arc_id}: {e}")
        continue

# Salvataggio
with open("dati/linearization_test2.json", "w") as f:
    json.dump(linearization, f, indent=4)

print("✅ File linearization_test2.json aggiornato con funzione TTI.")
