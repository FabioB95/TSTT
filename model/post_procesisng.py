import json
import matplotlib.pyplot as plt
import pandas as pd
import networkx as nx

# === Percorsi ===
RESULTS_PATH = "dati/results.json"
TRIPS_PATH = "dati/trips_with_paths.json"

# === Caricamento ===
with open(RESULTS_PATH, "r") as f:
    results = json.load(f)

with open(TRIPS_PATH, "r") as f:
    trips = json.load(f)

# === Mappa trip_id -> trip_data ===
trip_map = {trip["ID"]: trip for trip in trips}

# === Creazione DataFrame ===
df = pd.DataFrame(results)
df["trip_index"] = df["trip_id"].apply(lambda x: int(x.replace("trip_", "")))
df = df.sort_values("trip_index")

# === Tabella riepilogativa ===
print("\n📊 Tabella dei risultati:")
print(df[["trip_id", "selected_path", "departure_time", "travel_time", "FP_normalized"]].to_string(index=False))

# === Salvataggio CSV ===
df.to_csv("dati/results_table.csv", index=False)
print("\n✅ Salvato anche in: dati/results_table.csv")

# === Grafico 1: Travel Time ===
plt.figure(figsize=(10, 5))
plt.bar(df["trip_index"], df["travel_time"], color="skyblue")
plt.xlabel("Trip ID")
plt.ylabel("Travel Time")
plt.title("Travel Time per Trip")
plt.tight_layout()
plt.savefig("dati/travel_time_barplot.png")
plt.show()

# === Grafico 2: Histogram of Departure Times ===
plt.figure(figsize=(8, 4))
plt.hist(df["departure_time"], bins=20, color="salmon", edgecolor="black")
plt.title("Distribuzione delle partenze")
plt.xlabel("Tempo di partenza")
plt.ylabel("Numero di viaggi")
plt.tight_layout()
plt.savefig("dati/departure_histogram.png")
plt.show()

# === Mappa percorsi su grafo (opzionale) ===
try:
    G = nx.DiGraph()
    for trip in df.itertuples():
        arcs = []
        trip_data = trip_map[trip.trip_id]
        for path in trip_data["paths"]:
            if path["ID"] == trip.selected_path:
                arcs = path["arcs"]
                break
        for i, j in arcs:
            G.add_edge(i, j)
    plt.figure(figsize=(10, 10))
    pos = nx.spring_layout(G, seed=42)
    nx.draw_networkx_nodes(G, pos, node_size=30)
    nx.draw_networkx_edges(G, pos, arrowstyle='->', arrowsize=10)
    plt.title("🗺️ Path selezionati")
    plt.savefig("dati/selected_paths_graph.png")
    plt.show()
except Exception as e:
    print(f"⚠️ Impossibile visualizzare i percorsi selezionati: {e}")
