import json
import numpy as np
import matplotlib.pyplot as plt

# === Parametri globali ===
TIME_START = 0 * 60 + 0        # 0 minuti (00:00)
TIME_END = 26 * 60 + 45        # 1605 minuti 
MINUTES = list(range(TIME_START, TIME_END + 1, 15))  # 108 time slots
M = 0.5  # Intensità globale del traffico 

"""""
M lo spossiamo cambiare se volessimo generare: 
1. M = 0.5 --> low traffic 
2. M = 1 --> normal traffic
3. M  = 1.5 --> high traffic! 
""""" 
def smooth_step(x, x0, x1):
    if x <= x0:
        return 0.15
    elif x >= x1:
        return 1.0
    else:
        return 3*((x - x0)/(x1 - x0))**2 - 2*((x - x0)/(x1 - x0))**3

def create_profile(profile_type):
    traffic = np.zeros(len(MINUTES))

    for idx, t in enumerate(MINUTES):
        # Ciclo su due giorni (ogni giorno è 13 ore = 52 time slots da 15 minuti)
        day1_start = 6 * 60  # 360 minuti = 6:00
        day1_end = 19 * 60   # 1140 minuti = 19:00
        day2_start = day1_start + 1440  # 6:00 del giorno dopo
        day2_end = day1_end + 1440      # 19:00 del giorno dopo

        # Verifica se il tempo è dentro uno dei due giorni lavorativi
        if (day1_start <= t <= day1_end) or (day2_start <= t <= day2_end):
            # Usa l'orario relativo al giorno (ignora il giorno in sé)
            t_in_day = t % 1440  # 1440 minuti = 24 ore

            if profile_type == "morning":
                if 360 <= t_in_day <= 480:  # 6:00–8:00
                    traffic[idx] = smooth_step(t_in_day, 360, 480)
                elif 480 < t_in_day <= 600:  # 8:00–10:00
                    traffic[idx] = smooth_step(600 - t_in_day, 0.15, 120)
                else:
                    traffic[idx] = 0.15

            elif profile_type == "evening":
                if 900 <= t_in_day <= 1050:  # 15:00–17:30
                    traffic[idx] = smooth_step(t_in_day, 900, 1050)
                elif 1050 < t_in_day <= 1140:  # 17:30–19:00
                    traffic[idx] = smooth_step(1140 - t_in_day, 0.15, 90)
                else:
                    traffic[idx] = 0.15

            elif profile_type == "camel_day":
                traffic_morning = smooth_step(t_in_day, 360, 480) if 360 <= t_in_day <= 600 else 0.15
                if 480 < t_in_day <= 600:
                    traffic_morning = smooth_step(600 - t_in_day, 0.15, 120)

                traffic_evening = smooth_step(t_in_day, 900, 1050) if 900 <= t_in_day <= 1140 else 0.15
                if 1050 < t_in_day <= 1140:
                    traffic_evening = smooth_step(1140 - t_in_day, 0.15, 90)

                traffic[idx] = max(traffic_morning, traffic_evening)

        else:
            # Fuori dall'orario lavorativo, traffico minimo
            traffic[idx] = 0.15

    return np.round(traffic, 3)

# === Caricamento archi ===
with open("dati/traffic_profile.json", "r") as f:
    arcs_data = json.load(f)["edges"]

arc_traffic = {}  

for arc in arcs_data:
    i, j = arc["from_node"], arc["to_node"]
    profile = arc.get("traffic_profile", {}).get("time_profile", "camel_day")
    level = arc.get("traffic_profile", {}).get("congestion_level", 5)

    base = create_profile(profile)
    scaling = level / 5
    scaled = [round(p * scaling * M, 3) for p in base]

    
        # now JSON keys are the snapshot index 0…107
    arc_traffic[f"{i},{j}"] = { str(idx): scaled[idx] for idx in range(len(MINUTES)) }

# === Salvataggio ===
#M = 0.5
with open("dati/arc_traffic_low.json", "w") as f:
    json.dump(arc_traffic, f, indent=2)

#M = 1
#with open("dati/arc_traffic_normal.json", "w") as f:
#    json.dump(arc_traffic, f, indent=2)

#M = 1.5
#with open("dati/arc_traffic_high.json", "w") as f:
#    json.dump(arc_traffic, f, indent=2)

# === Plot ===
import matplotlib.pyplot as plt

profiles = ["morning", "evening", "camel_day"]

for name in profiles:
    y = create_profile(name)

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(MINUTES, y, label=name, color="steelblue")
    ax.set_xticks(range(MINUTES[0], MINUTES[-1] + 1, 15))
    ax.set_xticklabels([f"{h//60}:{h%60:02d}" for h in range(MINUTES[0], MINUTES[-1] + 1, 15)], rotation=45)
    ax.set_title(f"Profilo di congestione: {name}")
    ax.set_ylabel("Fattore di congestione (0–1)")
    ax.set_xlabel("Orario")
    ax.grid(True)
    ax.legend()
    plt.tight_layout()

    # Salva immagine
    plt.savefig(f"dati/profile_{name}.png")
    plt.show()
