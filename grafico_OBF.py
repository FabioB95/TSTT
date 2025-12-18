# analyze_objective_functions.py
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from matplotlib.ticker import ScalarFormatter

print("\n" + "="*60)
print("📊 ANALISI OBJECTIVE FUNCTIONS")
print("="*60)

# === Lettura dati dal tuo dataset ===
# Copia qui i tuoi dati in formato tabellare
data = [
    # Traffico Basso - Benchmark Tutti Assieme
    {"Traffico": "Basso", "Modello": "Benchmark Tutti Assieme", "Trip": 100, "F.O.": 9.64E+11},
    {"Traffico": "Basso", "Modello": "Benchmark Tutti Assieme", "Trip": 250, "F.O.": 4.78E+13},
    {"Traffico": "Basso", "Modello": "Benchmark Tutti Assieme", "Trip": 500, "F.O.": 1.04E+14},
    {"Traffico": "Basso", "Modello": "Benchmark Tutti Assieme", "Trip": 1000, "F.O.": 4.89E+14},
    {"Traffico": "Basso", "Modello": "Benchmark Tutti Assieme", "Trip": 2000, "F.O.": 1.95708824E+15},
    
    # Traffico Basso - Benchmark Uniformi
    {"Traffico": "Basso", "Modello": "Benchmark Uniformi", "Trip": 100, "F.O.": 3.62644E+11},
    {"Traffico": "Basso", "Modello": "Benchmark Uniformi", "Trip": 250, "F.O.": 3.76E+13},
    {"Traffico": "Basso", "Modello": "Benchmark Uniformi", "Trip": 500, "F.O.": 7.89E+13},
    {"Traffico": "Basso", "Modello": "Benchmark Uniformi", "Trip": 1000, "F.O.": 4.27E+14},
    {"Traffico": "Basso", "Modello": "Benchmark Uniformi", "Trip": 2000, "F.O.": 1.86E+15},
    
    # Traffico Basso - Ottimizzazione
    {"Traffico": "Basso", "Modello": "Ottimizzazione", "Trip": 100, "F.O.": 1.52E+07},
    {"Traffico": "Basso", "Modello": "Ottimizzazione", "Trip": 250, "F.O.": 9.10E+12},
    {"Traffico": "Basso", "Modello": "Ottimizzazione", "Trip": 500, "F.O.": 3.03E+13},
    {"Traffico": "Basso", "Modello": "Ottimizzazione", "Trip": 1000, "F.O.": 3.38175612E+14},
    {"Traffico": "Basso", "Modello": "Ottimizzazione", "Trip": 2000, "F.O.": 1.77E+15},
    
    # Senza Traffico - Benchmark Tutti Assieme
    {"Traffico": "Zero", "Modello": "Benchmark Tutti Assieme", "Trip": 100, "F.O.": None},
    {"Traffico": "Zero", "Modello": "Benchmark Tutti Assieme", "Trip": 250, "F.O.": None},
    {"Traffico": "Zero", "Modello": "Benchmark Tutti Assieme", "Trip": 500, "F.O.": None},
    {"Traffico": "Zero", "Modello": "Benchmark Tutti Assieme", "Trip": 1000, "F.O.": None},
    {"Traffico": "Zero", "Modello": "Benchmark Tutti Assieme", "Trip": 2000, "F.O.": None},
    
    # Senza Traffico - Benchmark Uniformi
    {"Traffico": "Zero", "Modello": "Benchmark Uniformi", "Trip": 100, "F.O.": None},
    {"Traffico": "Zero", "Modello": "Benchmark Uniformi", "Trip": 250, "F.O.": None},
    {"Traffico": "Zero", "Modello": "Benchmark Uniformi", "Trip": 500, "F.O.": None},
    {"Traffico": "Zero", "Modello": "Benchmark Uniformi", "Trip": 1000, "F.O.": None},
    {"Traffico": "Zero", "Modello": "Benchmark Uniformi", "Trip": 2000, "F.O.": None},
    
    # Senza Traffico - Ottimizzazione
    {"Traffico": "Zero", "Modello": "Ottimizzazione", "Trip": 100, "F.O.": 1.14E+07},
    {"Traffico": "Zero", "Modello": "Ottimizzazione", "Trip": 250, "F.O.": None},
    {"Traffico": "Zero", "Modello": "Ottimizzazione", "Trip": 500, "F.O.": None},
    {"Traffico": "Zero", "Modello": "Ottimizzazione", "Trip": 1000, "F.O.": None},
    {"Traffico": "Zero", "Modello": "Ottimizzazione", "Trip": 2000, "F.O.": None},
    
    # Traffico Medio - Benchmark Tutti Assieme
    {"Traffico": "Medio", "Modello": "Benchmark Tutti Assieme", "Trip": 100, "F.O.": 9.87E+11},
    {"Traffico": "Medio", "Modello": "Benchmark Tutti Assieme", "Trip": 250, "F.O.": 4.81E+13},
    {"Traffico": "Medio", "Modello": "Benchmark Tutti Assieme", "Trip": 500, "F.O.": 1.04E+14},
    {"Traffico": "Medio", "Modello": "Benchmark Tutti Assieme", "Trip": 1000, "F.O.": 4.89E+14},
    {"Traffico": "Medio", "Modello": "Benchmark Tutti Assieme", "Trip": 2000, "F.O.": 1.96E+15},
    
    # Traffico Medio - Benchmark Uniformi
    {"Traffico": "Medio", "Modello": "Benchmark Uniformi", "Trip": 100, "F.O.": 3.95576217E+11},
    {"Traffico": "Medio", "Modello": "Benchmark Uniformi", "Trip": 250, "F.O.": 3.80972382E+13},
    {"Traffico": "Medio", "Modello": "Benchmark Uniformi", "Trip": 500, "F.O.": 7.98E+13},
    {"Traffico": "Medio", "Modello": "Benchmark Uniformi", "Trip": 1000, "F.O.": 4.29503244E+14},
    {"Traffico": "Medio", "Modello": "Benchmark Uniformi", "Trip": 2000, "F.O.": 1.86E+15},
    
    # Traffico Medio - Ottimizzazione
    {"Traffico": "Medio", "Modello": "Ottimizzazione", "Trip": 100, "F.O.": 1.56E+07},
    {"Traffico": "Medio", "Modello": "Ottimizzazione", "Trip": 250, "F.O.": None},  # Dato mancante
    {"Traffico": "Medio", "Modello": "Ottimizzazione", "Trip": 500, "F.O.": 3.11E+13},
    {"Traffico": "Medio", "Modello": "Ottimizzazione", "Trip": 1000, "F.O.": 3.47E+14},
    {"Traffico": "Medio", "Modello": "Ottimizzazione", "Trip": 2000, "F.O.": 1.81E+15},
    
    # Traffico Alto - tutti None per ora
    {"Traffico": "Alto", "Modello": "Benchmark Tutti Assieme", "Trip": 100, "F.O.": None},
    {"Traffico": "Alto", "Modello": "Benchmark Tutti Assieme", "Trip": 250, "F.O.": None},
    {"Traffico": "Alto", "Modello": "Benchmark Tutti Assieme", "Trip": 500, "F.O.": None},
    {"Traffico": "Alto", "Modello": "Benchmark Tutti Assieme", "Trip": 1000, "F.O.": None},
    {"Traffico": "Alto", "Modello": "Benchmark Tutti Assieme", "Trip": 2000, "F.O.": None},
    
    {"Traffico": "Alto", "Modello": "Benchmark Uniformi", "Trip": 100, "F.O.": None},
    {"Traffico": "Alto", "Modello": "Benchmark Uniformi", "Trip": 250, "F.O.": None},
    {"Traffico": "Alto", "Modello": "Benchmark Uniformi", "Trip": 500, "F.O.": None},
    {"Traffico": "Alto", "Modello": "Benchmark Uniformi", "Trip": 1000, "F.O.": None},
    {"Traffico": "Alto", "Modello": "Benchmark Uniformi", "Trip": 2000, "F.O.": None},
    
    {"Traffico": "Alto", "Modello": "Ottimizzazione", "Trip": 100, "F.O.": None},
    {"Traffico": "Alto", "Modello": "Ottimizzazione", "Trip": 250, "F.O.": None},
    {"Traffico": "Alto", "Modello": "Ottimizzazione", "Trip": 500, "F.O.": None},
    {"Traffico": "Alto", "Modello": "Ottimizzazione", "Trip": 1000, "F.O.": None},
    {"Traffico": "Alto", "Modello": "Ottimizzazione", "Trip": 2000, "F.O.": None},
]

# === Creazione DataFrame ===
df = pd.DataFrame(data)
print(f"📊 Dati letti: {len(df)} righe")

# === Salvataggio CSV ===
output_dir = "analisi_risultati"
os.makedirs(output_dir, exist_ok=True)
csv_file = os.path.join(output_dir, "objective_functions.csv")
df.to_csv(csv_file, index=False)
print(f"✅ CSV salvato: {csv_file}")

# === Creazione grafici ===
plt.rcParams['figure.figsize'] = [15, 10]
plt.rcParams['font.size'] = 12

# Colori per i modelli
colors = {
    'Ottimizzazione': 'blue',
    'Benchmark Tutti Assieme': 'red',
    'Benchmark Uniformi': 'green'
}

# Marker per i modelli
markers = {
    'Ottimizzazione': 'o',
    'Benchmark Tutti Assieme': 's',
    'Benchmark Uniformi': '^'
}

# === 1. Grafico per ogni livello di traffico ===
livelli_traffico = ['Basso', 'Zero', 'Medio', 'Alto']

for traffico in livelli_traffico:
    df_traffico = df[df['Traffico'] == traffico]
    if df_traffico.empty or df_traffico['F.O.'].isna().all():
        print(f"⚠️ Nessun dato per traffico {traffico}")
        continue
    
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Plot per ogni modello
    for modello in df_traffico['Modello'].unique():
        df_modello = df_traffico[df_traffico['Modello'] == modello]
        df_modello = df_modello.dropna(subset=['F.O.'])
        
        if not df_modello.empty:
            ax.plot(df_modello['Trip'], df_modello['F.O.'], 
                   marker=markers.get(modello, 'o'),
                   color=colors.get(modello, 'black'),
                   linewidth=3, markersize=10,
                   label=modello)
    
    ax.set_xlabel('Numero di Trip', fontsize=14)
    ax.set_ylabel('Objective Function', fontsize=14)
    ax.set_title(f'Objective Function - Traffico {traffico}', fontsize=16, pad=20)
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.set_xscale('log')
    ax.set_yscale('log')
    
    # Formattazione assi
    ax.xaxis.set_major_formatter(ScalarFormatter())
    ax.yaxis.set_major_formatter(ScalarFormatter())
    
    plt.tight_layout()
    output_file = os.path.join(output_dir, f"fo_traffico_{traffico.lower()}.png")
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ Grafico traffico {traffico} salvato: {output_file}")

# === 2. Grafico comparativo tutti i livelli ===
fig, axes = plt.subplots(2, 2, figsize=(20, 16))
axes = axes.ravel()

for idx, traffico in enumerate(['Basso', 'Zero', 'Medio']):
    if idx < len(axes):
        ax = axes[idx]
        df_traffico = df[df['Traffico'] == traffico]
        
        if df_traffico.empty or df_traffico['F.O.'].isna().all():
            ax.text(0.5, 0.5, 'Nessun dato disponibile', 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f'Traffico {traffico}')
            continue
        
        # Plot per ogni modello
        for modello in df_traffico['Modello'].unique():
            df_modello = df_traffico[df_traffico['Modello'] == modello]
            df_modello = df_modello.dropna(subset=['F.O.'])
            
            if not df_modello.empty:
                ax.plot(df_modello['Trip'], df_modello['F.O.'], 
                       marker=markers.get(modello, 'o'),
                       color=colors.get(modello, 'black'),
                       linewidth=2, markersize=8,
                       label=modello)
        
        ax.set_xlabel('Numero di Trip')
        ax.set_ylabel('Objective Function')
        ax.set_title(f'Traffico {traffico}', fontsize=14)
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_xscale('log')
        ax.set_yscale('log')

# Nascondi l'ultimo subplot se non usato
if len(livelli_traffico) < 4:
    axes[3].set_visible(False)

plt.tight_layout()
output_file = os.path.join(output_dir, "fo_comparativo_tutti.png")
plt.savefig(output_file, dpi=300, bbox_inches='tight')
plt.close()
print(f"✅ Grafico comparativo salvato: {output_file}")

# === 3. Grafico rapporti (Ottimizzazione vs Altri) ===
fig, ax = plt.subplots(figsize=(14, 10))

# Calcola rapporti per traffico basso (dati più completi)
df_basso = df[df['Traffico'] == 'Basso']
trip_numbers = sorted(df_basso['Trip'].unique())

for trip in trip_numbers:
    df_trip = df_basso[df_basso['Trip'] == trip]
    
    # Trova valori per ogni modello
    ott_fo = df_trip[df_trip['Modello'] == 'Ottimizzazione']['F.O.'].iloc[0] if not df_trip[df_trip['Modello'] == 'Ottimizzazione'].empty else None
    assieme_fo = df_trip[df_trip['Modello'] == 'Benchmark Tutti Assieme']['F.O.'].iloc[0] if not df_trip[df_trip['Modello'] == 'Benchmark Tutti Assieme'].empty else None
    uniforme_fo = df_trip[df_trip['Modello'] == 'Benchmark Uniformi']['F.O.'].iloc[0] if not df_trip[df_trip['Modello'] == 'Benchmark Uniformi'].empty else None
    
    if ott_fo and assieme_fo:
        rapporto_assieme = assieme_fo / ott_fo if ott_fo > 0 else float('inf')
        ax.bar(trip - 10, rapporto_assieme, width=15, 
               color='red', alpha=0.7, label='Benchmark Tutti Assieme' if trip == trip_numbers[0] else "")
    
    if ott_fo and uniforme_fo:
        rapporto_uniforme = uniforme_fo / ott_fo if ott_fo > 0 else float('inf')
        ax.bar(trip + 10, rapporto_uniforme, width=15, 
               color='green', alpha=0.7, label='Benchmark Uniformi' if trip == trip_numbers[0] else "")

ax.set_xlabel('Numero di Trip', fontsize=14)
ax.set_ylabel('Rapporto F.O. (Benchmark/Ottimizzazione)', fontsize=14)
ax.set_title('Performance Relativa - Traffico Basso\n(< 1 = Ottimizzazione migliore)', fontsize=16, pad=20)
ax.legend(fontsize=12)
ax.grid(True, alpha=0.3)
ax.set_xscale('log')
ax.axhline(y=1, color='blue', linestyle='--', alpha=0.7, label='Parità')

plt.tight_layout()
output_file = os.path.join(output_dir, "fo_rapporti_traffico_basso.png")
plt.savefig(output_file, dpi=300, bbox_inches='tight')
plt.close()
print(f"✅ Grafico rapporti salvato: {output_file}")

# === 4. Tabella riassuntiva ===
print(f"\n📊 Tabella Riassuntiva Objective Functions:")
print("="*80)
print(f"{'Traffico':<10} {'Modello':<25} {'100':<15} {'250':<15} {'500':<15} {'1000':<15} {'2000':<15}")
print("="*80)

for traffico in ['Basso', 'Zero', 'Medio']:
    df_traffico = df[df['Traffico'] == traffico]
    for modello in df_traffico['Modello'].unique():
        df_modello = df_traffico[df_traffico['Modello'] == modello]
        valori = []
        for trip in [100, 250, 500, 1000, 2000]:
            fo_val = df_modello[df_modello['Trip'] == trip]['F.O.'].iloc[0] if not df_modello[df_modello['Trip'] == trip].empty and not pd.isna(df_modello[df_modello['Trip'] == trip]['F.O.'].iloc[0]) else "N/A"
            valori.append(f"{fo_val:.2e}" if isinstance(fo_val, (int, float)) else str(fo_val))
        
        print(f"{traffico:<10} {modello:<25} {valori[0]:<15} {valori[1]:<15} {valori[2]:<15} {valori[3]:<15} {valori[4]:<15}")

print("="*80)
print(f"\n📁 Tutti i file salvati in: {output_dir}")
print(f"📊 CSV: {csv_file}")