import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import json

# === Percorsi dei file ===
SIGMA_PATH = "output_sigma_DEF.csv"
X_PATH = "output_x_DEF.csv"

# === Creazione cartelle output ===
output_dir = "figure"
curve_dir = os.path.join(output_dir, "curve_TTI_per_arc")
os.makedirs(output_dir, exist_ok=True)
os.makedirs(curve_dir, exist_ok=True)

# === Caricamento dati ===
sigma_df = pd.read_csv(SIGMA_PATH)
x_df = pd.read_csv(X_PATH)

# === Mappa colori personalizzati ===
def categorize_tti(tti):
    if tti <= 1.2:
        return "Verde - fluido"
    elif tti <= 1.6:
        return "Arancio - congestionato"
    else:
        return "Rosso - molto congestionato"

sigma_df["congestion_level"] = sigma_df["tti"].apply(categorize_tti)

cmap_manual = {
    "Verde - fluido": "#8BC34A",
    "Arancio - congestionato": "#FFC107",
    "Rosso - molto congestionato": "#F44336"
}

# === Heatmap semantica per congestione ===
print("🎨 Generazione heatmap categorizzata...")
congestion_pivot = sigma_df.pivot(index="arc", columns="time", values="congestion_level")
color_matrix = congestion_pivot.applymap(lambda x: cmap_manual.get(x, "#FFFFFF"))

fig, ax = plt.subplots(figsize=(15, 10))
table = ax.table(cellText=None,
                 cellColours=color_matrix.values,
                 rowLabels=congestion_pivot.index,
                 colLabels=congestion_pivot.columns,
                 loc='center')
ax.axis('off')
plt.title("Heatmap Congestione Arco/Snapshot (colori: verde, arancio, rosso)", fontsize=14, weight="bold")
plt.tight_layout()
plt.savefig("figure/figura9_heatmap_categorie_congestione_DEF.png")
plt.close()

# === Curve TTI per ogni arco ===
print("📈 Salvataggio curve TTI per ogni arco...")
for arc in sigma_df["arc"].unique():
    arc_data = sigma_df[sigma_df["arc"] == arc].sort_values("time")
    plt.figure(figsize=(8, 4))
    plt.plot(arc_data["time"], arc_data["tti"], label=f"Arc {arc}")
    plt.xlabel("Snapshot")
    plt.ylabel("TTI (σ)")
    plt.title(f"TTI Trend - Arc {arc}")
    plt.grid(True)
    plt.tight_layout()
    arc_filename = arc.replace(">", "_").replace(":", "_")
    plt.savefig(f"{curve_dir}/tti_trend_{arc_filename}.png")
    plt.close()

# === TTI medio nel tempo ===
print("📊 Calcolo TTI medio nel tempo...")
tti_time_mean = sigma_df.groupby("time")["tti"].mean()
plt.figure(figsize=(10, 4))
plt.plot(tti_time_mean.index, tti_time_mean.values, marker='o', color='navy')
plt.xlabel("Snapshot temporale")
plt.ylabel("TTI medio")
plt.title("Andamento medio del Travel Time Index nel tempo")
plt.grid(True)
plt.tight_layout()
plt.savefig("figure/figura10_tti_medio_temporale_DEF.png")
plt.close()

# === Flusso totale su tutti gli archi nel tempo ===
print("🚗 Calcolo flusso veicolare totale per snapshot...")
flow_by_time = x_df.groupby("time")["flow"].sum()
plt.figure(figsize=(10, 4))
plt.plot(flow_by_time.index, flow_by_time.values, marker='s', color='darkorange')
plt.xlabel("Snapshot temporale")
plt.ylabel("Flusso totale veicoli")
plt.title("Flusso veicolare totale nel tempo")
plt.grid(True)
plt.tight_layout()
plt.savefig("figure/figura11_flusso_totale_temporale_DEF.png")
plt.close()

print("✅ Dashboard salvata in cartella 'figure/'")
