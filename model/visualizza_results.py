import json
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd
import os
import matplotlib.cm as cm
import numpy as np
import seaborn as sns
import pathlib
import dataframe_image as dfi

# === Directory per salvataggio immagini ===
output_dir = pathlib.Path("figure")
output_dir.mkdir(exist_ok=True)

# === Caricamento dati ===
with open("dati/nodes_test.json") as f:
    nodes = json.load(f)["nodes"]

with open("dati/arcs_test.json") as f:
    arcs = json.load(f)["edges"]

with open("dati/trips_test.json") as f:
    trips = json.load(f)["trips"]

# Caricamento sicuro di output_y
try:
    y_df = pd.read_csv("output_y.csv")
    if "trip" not in y_df.columns:
        y_df.columns = ["trip", "departure_time", "vehicles"]
    if y_df.empty:
        print("⚠️ y_df è vuoto: nessun percorso visualizzato nella Figura 3")
except:
    y_df = pd.DataFrame()

# === Costruzione grafo ===
G = nx.DiGraph()
for node in nodes:
    G.add_node(node["id"])
for arc in arcs:
    G.add_edge(arc["from"], arc["to"], fftt=arc["fftt"], capacity=arc["capacity"])
pos = nx.spring_layout(G, seed=42)

# === Generazione colori univoci per trip ===
num_trips = len(trips)
cmap = cm.get_cmap("tab10", num_trips)
trip_colors = [cmap(i) for i in range(num_trips)] if num_trips > 0 else []

# === Figura 1: grafo base ===
print("\n🧠 Figura 1: grafo dei nodi con FFTT e capacità")
plt.figure(figsize=(10, 6))
nx.draw(G, pos, with_labels=True, node_size=800, node_color="lightblue", arrows=True)
edge_labels = {(u, v): f"{d['fftt']} | {d['capacity']}" for u, v, d in G.edges(data=True)}
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
plt.title("Grafo con FFTT | Capacity")
plt.tight_layout()
plt.savefig(output_dir / "figura1_grafo_base.png")
plt.show()

# === Figura 2: tutti i percorsi OD disponibili ===
#print("\n🌐 Figura 2: tutti i percorsi OD disponibili")
#plt.figure(figsize=(10, 6))
#nx.draw(G, pos, with_labels=True, node_size=800, node_color="lightgray", arrows=True)
#for i, trip in enumerate(trips):
#    for path in trip["paths"]:
#        edges = [(a[0], a[1]) for a in path["arcs"]]
#        color = trip_colors[i % len(trip_colors)]
#        nx.draw_networkx_edges(G, pos, edgelist=edges, width=2.5, edge_color=[color], label=f"Trip {i}")
#plt.title("Tutti i percorsi OD possibili")
#plt.legend()
#plt.tight_layout()
#plt.savefig(output_dir / "figura2_tutti_percorsi.png")
#plt.show()

# === Figura 3: percorsi effettivamente scelti ===
print("\n🚗 Figura 3: percorsi effettivamente scelti dal modello")
if not y_df.empty:
    plt.figure(figsize=(10, 6))
    nx.draw(G, pos, with_labels=True, node_size=800, node_color="lightgray", arrows=True) 
    for _, row in y_df.iterrows():
        trip_index = int(row["trip"])
        path_index = int(row["path_index"])
        path = trips[trip_index]["paths"][path_index]
        edges = [(a[0], a[1]) for a in path["arcs"]]
        color = trip_colors[trip_index % len(trip_colors)]
        width = row["vehicles"] / 50
        nx.draw_networkx_edges(G, pos, edgelist=edges, width=width, edge_color=[color], alpha=0.7)
    plt.title("Percorsi effettivamente scelti (y[c,t])")
    plt.tight_layout()
    plt.savefig(output_dir / "figura3_percorsi_scelti.png")
    plt.show()

# === Figura 4: istogramma partenze ===
print("\n📊 Figura 4: istogramma delle partenze per snapshot temporale")
if not y_df.empty:
    y_df["trip_label"] = y_df["trip"].apply(lambda x: f"Trip {int(x)}")  # ← AGGIUNGI QUI
    plt.figure(figsize=(10, 4))
    y_df.groupby(["trip_label", "departure_time"]).sum()["vehicles"].unstack(0).plot(kind="bar", stacked=True)
    plt.title("Distribuzione delle partenze (snapshot τ)")
    plt.ylabel("Numero veicoli")
    plt.xlabel("Snapshot")
    plt.legend().remove()  
    plt.tight_layout()
    plt.savefig(output_dir / "figura4_istogramma_partenze.png")
    plt.show()


# === Figura 5: heatmap dei TTI stimati (σ) ===
print("\n🔥 Figura 5: heatmap dei TTI stimati (sigma)")
try:
    sigma_df = pd.read_csv("output_sigma.csv")
    if not sigma_df.empty:
        sigma_pivot = sigma_df.pivot(index="arc", columns="time", values="tti")
        plt.figure(figsize=(12, 6))
        plt.title("Heatmap Travel Time Index stimato (σ)")
        sns.heatmap(sigma_pivot, cmap="YlOrRd", linewidths=0.1, linecolor='gray', annot=False)
        plt.xlabel("Time Snapshot")
        plt.ylabel("Arc")
        plt.tight_layout()
        plt.savefig(output_dir / "figura5_heatmap_sigma.png")
        plt.show()
    else:
        print("⚠️ Nessun valore significativo in output_sigma.csv.")
except Exception as e:
    print(f"⚠️ Errore nel caricamento di output_sigma.csv: {e}")

# === Report JSON completo ===
print("\n📝 Generazione file report_trips.json")
trip_reports = []
for i, trip in enumerate(trips):
    possible_path = [ [(a[0], a[1]) for a in path["arcs"]] for path in trip["paths"] ]
    used_rows = y_df[y_df["trip"] == i]
    if used_rows.empty:
        trip_reports.append({
            "trip_id": i,
            "used": False,
            "path": possible_path,
            "chosen_departures": [],
            "total_vehicles": 0
        })
    else:
        departures = []
        total_vehicles = 0
        for _, row in used_rows.iterrows():
            departures.append({
                "path_index": int(row["path_index"]),
                "tau": int(row["departure_time"]),
                "vehicles": float(row["vehicles"])
            })
            total_vehicles += float(row["vehicles"])
        trip_reports.append({
            "trip_id": i,
            "used": True,
            "path": possible_path,
            "chosen_departures": departures,
            "total_vehicles": total_vehicles
        })

with open("report_trips.json", "w") as f:
    json.dump(trip_reports, f, indent=4)

print("✅ File `report_trips.json` generato con successo.")

#tabella# 

# === Aggiungi colonne ideal_departure e delay ===
with open("dati/trips_test.json") as f:
    trips_data = json.load(f)["trips"]

trip_ideal_times = {
    int(row["trip"]): min(trips_data[int(row["trip"])]["paths"][int(row["path_index"])]["possible_departure_times"])
    for _, row in y_df.iterrows()
}

y_df["ideal_departure"] = y_df["trip"].map(trip_ideal_times)
y_df["delay"] = y_df["departure_time"] - y_df["ideal_departure"]

import matplotlib.pyplot as plt

# Ordina per delay
df_delay = y_df[["trip", "ideal_departure", "departure_time", "delay"]].sort_values("delay")

# Colori per la colonna "delay"
norm = plt.Normalize(df_delay["delay"].min(), df_delay["delay"].max())
colors = plt.cm.Reds(norm(df_delay["delay"].values))

# Crea tabella
fig, ax = plt.subplots(figsize=(10, len(df_delay) * 0.4))
ax.axis('off')
ax.set_title("Tabella ritardi (snapshot)", fontsize=14, weight="bold")

# Dati
table_data = df_delay.round(0).astype(int).values.tolist()
col_labels = ["Trip", "Ideal", "Actual", "Delay"]
table = ax.table(cellText=table_data, colLabels=col_labels, loc='center')

# Colora la colonna "Delay"
for i in range(len(table_data)):
    table[(i + 1, 3)].set_facecolor(colors[i])
    table[(i + 1, 3)].set_text_props(color='black')

table.scale(1, 1.5)
plt.tight_layout()
plt.savefig(output_dir / "figura6_tabella_ritardi.png")
plt.close()
print("✅ Tabella ritardi salvata come figura6_tabella_ritardi.png")
