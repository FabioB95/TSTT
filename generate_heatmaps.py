# generate_heatmaps.py
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np
from pathlib import Path

print("\n" + "="*60)
print("🎨 GENERAZIONE HEATMAP AUTOMATICA")
print("="*60)

# === Configurazione ===
INPUT_FILES = [
    # Benchmark files
    "solution_benchmark_fixed_departure_100.xlsx",
    "solution_benchmark_fixed_departure_250.xlsx", 
    "solution_benchmark_fixed_departure_500.xlsx",
    "solution_benchmark_fixed_departure_1000.xlsx",
    
    # Ottimizzazione files
    "solution_ott_L_100_debug.xlsx",
    "solution_ott_L_250_debug.xlsx",
    "solution_ott_L_500_debug.xlsx", 
    "solution_ott_L_1000_debug.xlsx",
    "solution_ott_L_2000_debug.xlsx"
]

HEATMAP_SHEET = "heatmap"
OUTPUT_DIR = "heatmaps"

# === Creazione directory output ===
os.makedirs(OUTPUT_DIR, exist_ok=True)
print(f"📁 Directory output: {OUTPUT_DIR}")

# === Color palette per heatmap ===
plt.rcParams['figure.figsize'] = [20, 12]
plt.rcParams['font.size'] = 10

# === Processamento files ===
for file_path in INPUT_FILES:
    if not os.path.exists(file_path):
        print(f"⚠️ File non trovato: {file_path}")
        continue
    
    try:
        print(f"\n📊 Processando: {file_path}")
        
        # Estrai nome scenario
        if "benchmark" in file_path.lower():
            scenario_type = "benchmark"
            if "1000" in file_path:
                scenario_name = "benchmark_1000"
            elif "500" in file_path:
                scenario_name = "benchmark_500"
            elif "250" in file_path:
                scenario_name = "benchmark_250"
            elif "100" in file_path:
                scenario_name = "benchmark_100"
            else:
                scenario_name = f"benchmark_{file_path}"
        else:
            scenario_type = "ottimizzazione"
            if "2000" in file_path:
                scenario_name = "ottimizzazione_2000"
            elif "1000" in file_path:
                scenario_name = "ottimizzazione_1000"
            elif "500" in file_path:
                scenario_name = "ottimizzazione_500"
            elif "250" in file_path:
                scenario_name = "ottimizzazione_250"
            elif "100" in file_path:
                scenario_name = "ottimizzazione_100"
            else:
                scenario_name = f"ottimizzazione_{file_path}"
        
        # Leggi il foglio heatmap
        df_heatmap = pd.read_excel(file_path, sheet_name=HEATMAP_SHEET)
        print(f"✅ Letti {len(df_heatmap)} archi, {len(df_heatmap.columns)-1} tempi")
        
        if len(df_heatmap) == 0:
            print(f"⚠️ Nessun dato heatmap in {file_path}")
            continue
            
        # Prepara i dati per heatmap
        # Escludi la colonna 'Arco'
        time_cols = [col for col in df_heatmap.columns if col.startswith('t_')]
        
        if not time_cols:
            print(f"⚠️ Nessuna colonna temporale trovata in {file_path}")
            continue
            
        # Crea matrice heatmap
        heatmap_data = df_heatmap[time_cols].values
        archi_labels = df_heatmap['Arco'].tolist()
        
        # Gestione valori NaN/infiniti
        heatmap_data = np.nan_to_num(heatmap_data, nan=0.0, posinf=0.0, neginf=0.0)
        
        # === Generazione heatmap ===
        plt.figure(figsize=(25, 15))
        
        # Heatmap con seaborn
        sns.heatmap(heatmap_data, 
                   xticklabels=[t.replace('t_', '') for t in time_cols],
                   yticklabels=archi_labels,
                   cmap='YlOrRd',  # Colormap giallo-arancio-rosso
                   cbar_kws={'label': 'Flusso veicoli'},
                   vmin=0,
                   vmax=np.percentile(heatmap_data[heatmap_data > 0], 95) if np.any(heatmap_data > 0) else 1000)
        
        plt.title(f'Heatmap Traffico - {scenario_name}', fontsize=16, pad=20)
        plt.xlabel('Snapshot Temporale (15 minuti)', fontsize=12)
        plt.ylabel('Archi (origine→destinazione)', fontsize=12)
        
        # Rotazione labels per migliore leggibilità
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        
        # Aggiungi griglia
        plt.grid(True, alpha=0.3)
        
        # Layout ottimizzato
        plt.tight_layout()
        
        # Salva heatmap
        output_filename = os.path.join(OUTPUT_DIR, f"heatmap_{scenario_name}.png")
        plt.savefig(output_filename, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"✅ Heatmap salvata: {output_filename}")
        
        # === Statistiche ===
        max_flow = np.max(heatmap_data)
        avg_flow = np.mean(heatmap_data[heatmap_data > 0]) if np.any(heatmap_data > 0) else 0
        total_flow = np.sum(heatmap_data)
        
        print(f"   📊 Statistiche: max={max_flow:.1f}, media={avg_flow:.1f}, totale={total_flow:.0f}")
        
    except Exception as e:
        print(f"❌ Errore processando {file_path}: {str(e)}")
        continue

print(f"\n🎉 Generazione completata!")
print(f"📁 Heatmap salvate in: {OUTPUT_DIR}")

# === Creazione heatmap comparativa (opzionale) ===
print(f"\n🔄 Generazione heatmap comparativa...")

# Raccogli dati per confronto
comparison_data = {}

for file_path in INPUT_FILES:
    if not os.path.exists(file_path):
        continue
        
    try:
        if "benchmark" in file_path.lower():
            if "1000" in file_path:
                key = "benchmark_1000"
            elif "500" in file_path:
                key = "benchmark_500"
            elif "250" in file_path:
                key = "benchmark_250"
            elif "100" in file_path:
                key = "benchmark_100"
            else:
                continue
        elif "2000" in file_path:
            key = "ottimizzazione_2000"
        elif "1000" in file_path:
            key = "ottimizzazione_1000"
        elif "500" in file_path:
            key = "ottimizzazione_500"
        elif "250" in file_path:
            key = "ottimizzazione_250"
        elif "100" in file_path:
            key = "ottimizzazione_100"
        else:
            continue
            
        df_heatmap = pd.read_excel(file_path, sheet_name=HEATMAP_SHEET)
        time_cols = [col for col in df_heatmap.columns if col.startswith('t_')]
        if time_cols:
            avg_flow = df_heatmap[time_cols].mean().mean()
            max_flow = df_heatmap[time_cols].max().max()
            comparison_data[key] = {"avg": avg_flow, "max": max_flow}
            
    except:
        continue

# Crea grafico comparativo
if comparison_data:
    scenarios = list(comparison_data.keys())
    avg_flows = [comparison_data[s]["avg"] for s in scenarios]
    max_flows = [comparison_data[s]["max"] for s in scenarios]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))
    
    # Grafico flussi medi
    bars1 = ax1.bar(range(len(scenarios)), avg_flows, color=['red' if 'benchmark' in s else 'blue' for s in scenarios])
    ax1.set_title('Flusso Medio per Scenario')
    ax1.set_ylabel('Flusso Medio')
    ax1.set_xticks(range(len(scenarios)))
    ax1.set_xticklabels([s.replace('ottimizzazione', 'Ott').replace('benchmark', 'Bench') for s in scenarios], rotation=45)
    
    # Grafico flussi massimi
    bars2 = ax2.bar(range(len(scenarios)), max_flows, color=['red' if 'benchmark' in s else 'blue' for s in scenarios])
    ax2.set_title('Flusso Massimo per Scenario')
    ax2.set_ylabel('Flusso Massimo')
    ax2.set_xticks(range(len(scenarios)))
    ax2.set_xticklabels([s.replace('ottimizzazione', 'Ott').replace('benchmark', 'Bench') for s in scenarios], rotation=45)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "confronto_scenari.png"), dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"✅ Confronto scenari salvato: {os.path.join(OUTPUT_DIR, 'confronto_scenari.png')}")

print(f"\n🎉 TUTTE LE HEATMAP SONO STATE GENERATE!")
print(f"📁 Directory: {OUTPUT_DIR}")