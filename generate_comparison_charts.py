# generate_comparison_charts.py
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from pathlib import Path

print("\n" + "="*60)
print("📊 GENERAZIONE GRAFICI COMPARATIVI")
print("="*60)

# === Configurazione ===
# Lista precisa dei file e loro identificazione (CORRETTA)
INPUT_FILES = [
    # Benchmark files - CORRETTI
    ("solution_benchmark_fixed_departure_100.xlsx", "Benchmark", 100),
    ("solution_benchmark_fixed_departure_250.xlsx", "Benchmark", 250), 
    ("solution_benchmark_fixed_departure_500.xlsx", "Benchmark", 500),
    ("solution_benchmark_fixed_departure_1000.xlsx", "Benchmark", 1000),
    
    # Ottimizzazione files - CORRETTI
    ("solution_ott_L_100_debug.xlsx", "Ottimizzazione", 100),
    ("solution_ott_L_250_debug.xlsx", "Ottimizzazione", 250),
    ("solution_ott_L_500_debug.xlsx", "Ottimizzazione", 500), 
    ("solution_ott_L_1000_debug.xlsx", "Ottimizzazione", 1000),
    ("solution_ott_L_2000_debug.xlsx", "Ottimizzazione", 2000)
]

# === CORREZIONE TEMPORANEA: File scambiati per 100 e 1000 trip ===
# Mappatura corretta dei file effettivi
# generate_comparison_charts.py (versione originale)
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from pathlib import Path

print("\n" + "="*60)
print("📊 GENERAZIONE GRAFICI COMPARATIVI")
print("="*60)

# === Configurazione ===
# Lista precisa dei file e loro identificazione
INPUT_FILES = [
    # Benchmark files
    ("solution_benchmark_fixed_departure_100.xlsx", "Benchmark", 100),
    ("solution_benchmark_fixed_departure_250.xlsx", "Benchmark", 250), 
    ("solution_benchmark_fixed_departure_500.xlsx", "Benchmark", 500),
    ("solution_benchmark_fixed_departure_1000.xlsx", "Benchmark", 1000),
    
    # Ottimizzazione files
    ("solution_ott_L_100_debug.xlsx", "Ottimizzazione", 100),
    ("solution_ott_L_250_debug.xlsx", "Ottimizzazione", 250),
    ("solution_ott_L_500_debug.xlsx", "Ottimizzazione", 500), 
    ("solution_ott_L_1000_debug.xlsx", "Ottimizzazione", 1000),
    ("solution_ott_L_2000_debug.xlsx", "Ottimizzazione", 2000)
]

SUMMARY_SHEET = "Summary"
OUTPUT_DIR = "grafici_comparativi"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# === Lettura dati ===
all_data = []
missing_files = []

print("📂 Lettura file Excel...")

for file_path, metodo, trip_number in INPUT_FILES:
    if not os.path.exists(file_path):
        print(f"⚠️ File non trovato: {file_path}")
        missing_files.append(file_path)
        continue
    
    try:
        # Leggi il foglio Summary
        df_summary = pd.read_excel(file_path, sheet_name=SUMMARY_SHEET)
        
        # Converti in dizionario
        summary_dict = dict(zip(df_summary['Metrica'], df_summary['Valore']))
        summary_dict['Scenario_Name'] = f"{metodo} {trip_number}"
        summary_dict['Metodo'] = metodo
        summary_dict['Trip_Number'] = trip_number
            
        all_data.append(summary_dict)
        print(f"✅ Letto: {metodo} {trip_number} trip")
        
    except Exception as e:
        print(f"❌ Errore leggendo {file_path}: {str(e)}")
        continue

# ... (resto del codice rimane uguale)
if not all_data:
    print("❌ Nessun dato disponibile!")
    exit()

print(f"\n📊 Dati letti: {len(all_data)} scenari")

# === Conversione dati in DataFrame ===
df_all = pd.DataFrame(all_data)

# === Pulizia e conversione dati ===
numeric_columns = [
    'Domanda', 'Z', 'Endogeno', 'TSTT', 'Tempo (s)', 
    'Ave_Util_Mean', 'Max_Util', 'Ave_Ave_Flow', 'Max_Ave_Flow',
    'Ave_Ave_Util', 'Max_Ave_Util', 'Ave_Max_Flow', 'Max_Max_Flow',
    'Ave_Max_Util', 'Max_Max_Util', 'Ave_AumentoTTArco (%)', 
    'Max_AumentoTTArco (%)', 'Inconvenience_Mean', 'Inconvenience_Max'
]

for col in numeric_columns:
    if col in df_all.columns:
        df_all[col] = pd.to_numeric(df_all[col], errors='coerce')

# === Separazione Ottimizzazione vs Benchmark ===
df_ott = df_all[df_all['Metodo'] == 'Ottimizzazione'].copy()
df_bench = df_all[df_all['Metodo'] == 'Benchmark'].copy()

# Ordina per numero di trip
df_ott = df_ott.sort_values('Trip_Number')
df_bench = df_bench.sort_values('Trip_Number')

print(f"\n📊 Dati pronti:")
print(f"   Ottimizzazione: {len(df_ott)} scenari")
print(f"   Benchmark: {len(df_bench)} scenari")

# === Verifica dati letti correttamente ===
print(f"\n📋 Verifica dati:")
print("Ottimizzazione:")
for _, row in df_ott.iterrows():
    print(f"   {row['Trip_Number']} trip: Inconvenience = {row['Inconvenience_Mean']:.2f}")

print("Benchmark:")
for _, row in df_bench.iterrows():
    print(f"   {row['Trip_Number']} trip: Inconvenience = {row['Inconvenience_Mean']:.2f}")

# === Configurazione grafici ===
plt.rcParams['figure.figsize'] = [12, 8]
plt.rcParams['font.size'] = 10

# === Calcolo TSTT_Normalizzato per entrambi i dataset ===
print(f"\n🔍 Calcolo TSTT_Normalizzato...")

# Per Ottimizzazione
if 'TSTT' in df_ott.columns and 'Domanda' in df_ott.columns:
    df_ott['TSTT_Normalizzato'] = df_ott['TSTT'] / df_ott['Domanda']
    print("✅ TSTT_Normalizzato calcolato per Ottimizzazione")

# Per Benchmark  
if 'TSTT' in df_bench.columns and 'Domanda' in df_bench.columns:
    df_bench['TSTT_Normalizzato'] = df_bench['TSTT'] / df_bench['Domanda']
    print("✅ TSTT_Normalizzato calcolato per Benchmark")

# === Verifica TSTT_Normalizzato ===
print(f"\n🔍 Verifica TSTT_Normalizzato:")
print("Ottimizzazione TSTT_Normalizzato:")
for _, row in df_ott.iterrows():
    tstt_norm = row.get('TSTT_Normalizzato', 'N/A')
    if not pd.isna(tstt_norm):
        print(f"   {row['Trip_Number']} trip: {tstt_norm:.2f}")
    else:
        print(f"   {row['Trip_Number']} trip: N/A")

print("Benchmark TSTT_Normalizzato:")
for _, row in df_bench.iterrows():
    tstt_norm = row.get('TSTT_Normalizzato', 'N/A')
    if not pd.isna(tstt_norm):
        print(f"   {row['Trip_Number']} trip: {tstt_norm:.2f}")
    else:
        print(f"   {row['Trip_Number']} trip: N/A")

# === 1. Grafico Performance Principale: Inconvenience vs Trip ===
fig, ax = plt.subplots(figsize=(14, 10))

# Plot Inconvenience Medio
if len(df_ott) > 0:
    ax.plot(df_ott['Trip_Number'], df_ott['Inconvenience_Mean'], 
            'b-o', label='Ottimizzazione - Inconvenience Medio', linewidth=3, markersize=8)
if len(df_bench) > 0:
    ax.plot(df_bench['Trip_Number'], df_bench['Inconvenience_Mean'], 
            'r-s', label='Benchmark - Inconvenience Medio', linewidth=3, markersize=8)

# Plot Inconvenience Massimo
if len(df_ott) > 0:
    ax.plot(df_ott['Trip_Number'], df_ott['Inconvenience_Max'], 
            'b--o', label='Ottimizzazione - Inconvenience Max', alpha=0.7)
if len(df_bench) > 0:
    ax.plot(df_bench['Trip_Number'], df_bench['Inconvenience_Max'], 
            'r--s', label='Benchmark - Inconvenience Max', alpha=0.7)

ax.set_xlabel('Numero di Trip', fontsize=12)
ax.set_ylabel('Inconvenience', fontsize=12)
ax.set_title('Confronto Inconvenience: Ottimizzazione vs Benchmark', fontsize=14, pad=20)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
ax.set_xscale('log')

plt.tight_layout()
output_file = os.path.join(OUTPUT_DIR, "confronto_inconvenience.png")
plt.savefig(output_file, dpi=300, bbox_inches='tight')
plt.close()
print(f"✅ Grafico inconvenience salvato: {output_file}")

# === 2. Grafico Utilizzazione ===
fig, ax = plt.subplots(figsize=(14, 10))

if len(df_ott) > 0:
    ax.plot(df_ott['Trip_Number'], df_ott['Ave_Util_Mean'], 
            'b-o', label='Ottimizzazione - Utilizzazione Media', linewidth=3, markersize=8)
if len(df_bench) > 0:
    ax.plot(df_bench['Trip_Number'], df_bench['Ave_Util_Mean'], 
            'r-s', label='Benchmark - Utilizzazione Media', linewidth=3, markersize=8)

if len(df_ott) > 0:
    ax.plot(df_ott['Trip_Number'], df_ott['Max_Util'], 
            'b--o', label='Ottimizzazione - Utilizzazione Massima', alpha=0.7)
if len(df_bench) > 0:
    ax.plot(df_bench['Trip_Number'], df_bench['Max_Util'], 
            'r--s', label='Benchmark - Utilizzazione Massima', alpha=0.7)

ax.set_xlabel('Numero di Trip', fontsize=12)
ax.set_ylabel('Utilizzazione', fontsize=12)
ax.set_title('Confronto Utilizzazione: Ottimizzazione vs Benchmark', fontsize=14, pad=20)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
ax.set_xscale('log')

plt.tight_layout()
output_file = os.path.join(OUTPUT_DIR, "confronto_utilizzazione.png")
plt.savefig(output_file, dpi=300, bbox_inches='tight')
plt.close()
print(f"✅ Grafico utilizzazione salvato: {output_file}")

# === 3. Grafico TSTT (Tempo Totale di Viaggio) ===
fig, ax = plt.subplots(figsize=(14, 10))

if len(df_ott) > 0 and 'TSTT_Normalizzato' in df_ott.columns:
    ax.plot(df_ott['Trip_Number'], df_ott['TSTT_Normalizzato'], 
            'b-o', label='Ottimizzazione - TSTT Normalizzato', linewidth=3, markersize=8)
if len(df_bench) > 0 and 'TSTT_Normalizzato' in df_bench.columns:
    ax.plot(df_bench['Trip_Number'], df_bench['TSTT_Normalizzato'], 
            'r-s', label='Benchmark - TSTT Normalizzato', linewidth=3, markersize=8)

ax.set_xlabel('Numero di Trip', fontsize=12)
ax.set_ylabel('TSTT Normalizzato (veicolo-minuti per veicolo)', fontsize=12)
ax.set_title('Confronto TSTT Normalizzato: Ottimizzazione vs Benchmark', fontsize=14, pad=20)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
ax.set_xscale('log')
ax.set_yscale('log')

plt.tight_layout()
output_file = os.path.join(OUTPUT_DIR, "confronto_TSTT.png")
plt.savefig(output_file, dpi=300, bbox_inches='tight')
plt.close()
print(f"✅ Grafico TSTT salvato: {output_file}")

# === 4. Grafico Flussi ===
fig, ax = plt.subplots(figsize=(14, 10))

if len(df_ott) > 0:
    ax.plot(df_ott['Trip_Number'], df_ott['Ave_Ave_Flow'], 
            'b-o', label='Ottimizzazione - Flusso Medio Medio', linewidth=3, markersize=8)
if len(df_bench) > 0:
    ax.plot(df_bench['Trip_Number'], df_bench['Ave_Ave_Flow'], 
            'r-s', label='Benchmark - Flusso Medio Medio', linewidth=3, markersize=8)

if len(df_ott) > 0:
    ax.plot(df_ott['Trip_Number'], df_ott['Max_Max_Flow'], 
            'b--o', label='Ottimizzazione - Flusso Massimo Massimo', alpha=0.7)
if len(df_bench) > 0:
    ax.plot(df_bench['Trip_Number'], df_bench['Max_Max_Flow'], 
            'r--s', label='Benchmark - Flusso Massimo Massimo', alpha=0.7)

ax.set_xlabel('Numero di Trip', fontsize=12)
ax.set_ylabel('Flusso (veicoli/15min)', fontsize=12)
ax.set_title('Confronto Flussi: Ottimizzazione vs Benchmark', fontsize=14, pad=20)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
ax.set_xscale('log')

plt.tight_layout()
output_file = os.path.join(OUTPUT_DIR, "confronto_flussi.png")
plt.savefig(output_file, dpi=300, bbox_inches='tight')
plt.close()
print(f"✅ Grafico flussi salvato: {output_file}")

# === 5. Grafico Congestione (Aumento Tempi) ===
fig, ax = plt.subplots(figsize=(14, 10))

if len(df_ott) > 0:
    ax.plot(df_ott['Trip_Number'], df_ott['Ave_AumentoTTArco (%)'], 
            'b-o', label='Ottimizzazione - Aumento Tempo Medio', linewidth=3, markersize=8)
if len(df_bench) > 0:
    ax.plot(df_bench['Trip_Number'], df_bench['Ave_AumentoTTArco (%)'], 
            'r-s', label='Benchmark - Aumento Tempo Medio', linewidth=3, markersize=8)

ax.set_xlabel('Numero di Trip', fontsize=12)
ax.set_ylabel('Aumento Tempo (%)', fontsize=12)
ax.set_title('Confronto Congestione: Ottimizzazione vs Benchmark', fontsize=14, pad=20)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)
ax.set_xscale('log')
ax.set_yscale('log')

plt.tight_layout()
output_file = os.path.join(OUTPUT_DIR, "confronto_congestione.png")
plt.savefig(output_file, dpi=300, bbox_inches='tight')
plt.close()
print(f"✅ Grafico congestione salvato: {output_file}")

# === 6. Grafico Radar comparativo (per uno scenario specifico) ===
def create_radar_chart(ott_row, bench_row, trip_num):
    if ott_row.empty or bench_row.empty:
        return
    
    categories = [
        'Inconvenience_Mean',
        'Ave_Util_Mean', 
        'Ave_AumentoTTArco (%)',
        'Ave_Ave_Flow'
    ]
    
    # Normalizzazione valori (0-1)
    max_vals = {}
    for cat in categories:
        val1 = ott_row[cat].iloc[0] if not pd.isna(ott_row[cat].iloc[0]) else 0
        val2 = bench_row[cat].iloc[0] if not pd.isna(bench_row[cat].iloc[0]) else 0
        max_val = max(val1, val2)
        max_vals[cat] = max_val if max_val > 0 else 1
    
    ott_values = []
    bench_values = []
    for cat in categories:
        ott_val = ott_row[cat].iloc[0] if not pd.isna(ott_row[cat].iloc[0]) else 0
        bench_val = bench_row[cat].iloc[0] if not pd.isna(bench_row[cat].iloc[0]) else 0
        ott_values.append(ott_val / max_vals[cat])
        bench_values.append(bench_val / max_vals[cat])
    
    # Chiudi il cerchio
    categories_labels = ['Inconvenience', 'Utilizzazione', 'Congestione', 'Flusso']
    ott_values += [ott_values[0]]  # Chiudi il cerchio
    bench_values += [bench_values[0]]  # Chiudi il cerchio
    
    angles = [n / float(len(categories)) * 2 * np.pi for n in range(len(categories))]
    angles += angles[:1]  # Chiudi gli angoli
    
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
    
    ax.plot(angles, ott_values, 'b-o', linewidth=2, label='Ottimizzazione')
    ax.fill(angles, ott_values, 'b', alpha=0.1)
    
    ax.plot(angles, bench_values, 'r-s', linewidth=2, label='Benchmark')
    ax.fill(angles, bench_values, 'r', alpha=0.1)
    
    ax.set_xticks(angles[:-1])  # Usa solo gli angoli originali
    ax.set_xticklabels(categories_labels)  # Usa solo le etichette originali
    ax.set_title(f'Profilo Performance: {trip_num} Trip', size=16, pad=20)
    ax.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
    
    plt.tight_layout()
    output_file = os.path.join(OUTPUT_DIR, f"radar_{trip_num}_trip.png")
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ Grafico radar {trip_num} trip salvato: {output_file}")

# Crea radar charts per trip disponibili
available_trips_ott = set(df_ott['Trip_Number'])
available_trips_bench = set(df_bench['Trip_Number'])
common_trips = sorted(available_trips_ott.intersection(available_trips_bench))
radar_trips = [trip for trip in [100, 250, 500, 1000] if trip in common_trips]

for trip_num in radar_trips:
    ott_row = df_ott[df_ott['Trip_Number'] == trip_num]
    bench_row = df_bench[df_bench['Trip_Number'] == trip_num]
    if not ott_row.empty and not bench_row.empty:
        create_radar_chart(ott_row, bench_row, trip_num)

# === 7. Tabella comparativa CORRETTA ===
comparison_metrics = [
    'Trip_Number', 'Inconvenience_Mean', 'Max_Util', 
    'Ave_Util_Mean', 'TSTT_Normalizzato', 'Ave_AumentoTTArco (%)', 'Metodo'
]

df_comparison = pd.DataFrame(columns=comparison_metrics)

# Aggiungi dati ottimizzazione
for _, row in df_ott.iterrows():
    new_row = {}
    for metric in comparison_metrics:
        if metric == 'TSTT_Normalizzato':
            new_row[metric] = row.get('TSTT_Normalizzato', np.nan)
        elif metric != 'Metodo':
            new_row[metric] = row.get(metric, np.nan)
        else:
            new_row[metric] = 'Ottimizzazione'
    df_comparison = pd.concat([df_comparison, pd.DataFrame([new_row])], ignore_index=True)

# Aggiungi dati benchmark
for _, row in df_bench.iterrows():
    new_row = {}
    for metric in comparison_metrics:
        if metric == 'TSTT_Normalizzato':
            new_row[metric] = row.get('TSTT_Normalizzato', np.nan)
        elif metric != 'Metodo':
            new_row[metric] = row.get(metric, np.nan)
        else:
            new_row[metric] = 'Benchmark'
    df_comparison = pd.concat([df_comparison, pd.DataFrame([new_row])], ignore_index=True)

# Ordina per Trip_Number e Metodo
df_comparison = df_comparison.sort_values(['Trip_Number', 'Metodo'])

# Salva tabella comparativa
comparison_file = os.path.join(OUTPUT_DIR, "tabella_comparativa.csv")
df_comparison.to_csv(comparison_file, index=False)
print(f"✅ Tabella comparativa salvata: {comparison_file}")

# === 8. Grafico Vincitori ===
fig, ax = plt.subplots(figsize=(14, 10))

metrics_to_compare = [
    ('Inconvenience_Mean', 'Min'), 
    ('Ave_Util_Mean', 'Min'),
    ('TSTT_Normalizzato', 'Min'),
    ('Ave_AumentoTTArco (%)', 'Min')
]

winners_count = {'Ottimizzazione': 0, 'Benchmark': 0}

# Confronta solo i trip che hanno entrambi i metodi
common_trip_numbers = sorted(available_trips_ott.intersection(available_trips_bench))

for trip_num in common_trip_numbers:
    ott_row = df_ott[df_ott['Trip_Number'] == trip_num]
    bench_row = df_bench[df_bench['Trip_Number'] == trip_num]
    
    if not ott_row.empty and not bench_row.empty:
        for metric, criterion in metrics_to_compare:
            # Gestione TSTT_Normalizzato
            if metric == 'TSTT_Normalizzato':
                ott_val = ott_row['TSTT_Normalizzato'].iloc[0] if not pd.isna(ott_row['TSTT_Normalizzato'].iloc[0]) else np.inf
                bench_val = bench_row['TSTT_Normalizzato'].iloc[0] if not pd.isna(bench_row['TSTT_Normalizzato'].iloc[0]) else np.inf
            else:
                ott_val = ott_row[metric].iloc[0] if not pd.isna(ott_row[metric].iloc[0]) else np.inf
                bench_val = bench_row[metric].iloc[0] if not pd.isna(bench_row[metric].iloc[0]) else np.inf
            
            if criterion == 'Min':
                if not np.isinf(ott_val) and not np.isinf(bench_val):
                    if ott_val < bench_val:
                        winners_count['Ottimizzazione'] += 1
                    elif bench_val < ott_val:
                        winners_count['Benchmark'] += 1



# Aggiungi questo codice nel tuo script dopo il grafico TSTT esistente:

# === 9. Grafico Rapporto Performance (Ottimizzazione/Benchmark) ===
fig, ax = plt.subplots(figsize=(14, 10))

# Calcola il rapporto TSTT_Ottimizzazione / TSTT_Benchmark
trip_numbers = sorted(common_trip_numbers)
rapporti = []

for trip_num in trip_numbers:
    ott_row = df_ott[df_ott['Trip_Number'] == trip_num]
    bench_row = df_bench[df_bench['Trip_Number'] == trip_num]
    
    if not ott_row.empty and not bench_row.empty:
        ott_tstt = ott_row['TSTT_Normalizzato'].iloc[0]
        bench_tstt = bench_row['TSTT_Normalizzato'].iloc[0]
        
        if not pd.isna(ott_tstt) and not pd.isna(bench_tstt) and bench_tstt > 0:
            rapporto = ott_tstt / bench_tstt
            rapporti.append(rapporto)
        else:
            rapporti.append(np.nan)
    else:
        rapporti.append(np.nan)

# Plot del rapporto
valid_trip_numbers = [t for t, r in zip(trip_numbers, rapporti) if not pd.isna(r)]
valid_rapporti = [r for r in rapporti if not pd.isna(r)]

if valid_rapporti:
    ax.plot(valid_trip_numbers, valid_rapporti, 'g-o', linewidth=3, markersize=10, label='Rapporto Ottimizzazione/Benchmark')
    ax.axhline(y=1, color='r', linestyle='--', alpha=0.7, label='Parità (rapporto = 1)')
    
    ax.set_xlabel('Numero di Trip', fontsize=12)
    ax.set_ylabel('Rapporto TSTT_Normalizzato (Ottimizzazione/Benchmark)', fontsize=12)
    ax.set_title('Performance Relativa: Ottimizzazione vs Benchmark\n(< 1 = Ottimizzazione migliore, > 1 = Benchmark migliore)', fontsize=14, pad=20)
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.set_xscale('log')
    
    # Aggiungi valori sulle barre
    for i, (trip, rapporto) in enumerate(zip(valid_trip_numbers, valid_rapporti)):
        ax.annotate(f'{rapporto:.2f}', (trip, rapporto), textcoords="offset points", 
                   xytext=(0,10), ha='center', fontsize=10)
    
    plt.tight_layout()
    output_file = os.path.join(OUTPUT_DIR, "rapporto_performance.png")
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✅ Grafico rapporto performance salvato: {output_file}")

# === 10. Grafico Inconvenience Assoluto (più chiaro) ===
fig, ax = plt.subplots(figsize=(14, 10))

# Dati per il confronto più chiaro
trip_numbers = []
ott_inconvenience = []
bench_inconvenience = []
rapporti_inconvenience = []

for trip_num in sorted(common_trip_numbers):
    ott_row = df_ott[df_ott['Trip_Number'] == trip_num]
    bench_row = df_bench[df_bench['Trip_Number'] == trip_num]
    
    if not ott_row.empty and not bench_row.empty:
        ott_inc = ott_row['Inconvenience_Mean'].iloc[0]
        bench_inc = bench_row['Inconvenience_Mean'].iloc[0]
        
        if not pd.isna(ott_inc) and not pd.isna(bench_inc):
            trip_numbers.append(trip_num)
            ott_inconvenience.append(ott_inc)
            bench_inconvenience.append(bench_inc)
            rapporti_inconvenience.append(ott_inc / bench_inc if bench_inc > 0 else np.nan)

# Plot side-by-side
x = np.arange(len(trip_numbers))
width = 0.35

bars1 = ax.bar(x - width/2, ott_inconvenience, width, label='Ottimizzazione', color='blue', alpha=0.7)
bars2 = ax.bar(x + width/2, bench_inconvenience, width, label='Benchmark', color='red', alpha=0.7)

ax.set_xlabel('Numero di Trip', fontsize=12)
ax.set_ylabel('Inconvenience Medio', fontsize=12)
ax.set_title('Confronto Inconvenience: Ottimizzazione vs Benchmark', fontsize=14, pad=20)
ax.set_xticks(x)
ax.set_xticklabels(trip_numbers)
ax.legend(fontsize=12)
ax.grid(True, alpha=0.3)

# Aggiungi valori sulle barre
for i, (bar, value) in enumerate(zip(bars1, ott_inconvenience)):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
            f'{value:.1f}', ha='center', va='bottom', fontsize=9)

for i, (bar, value) in enumerate(zip(bars2, bench_inconvenience)):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
            f'{value:.1f}', ha='center', va='bottom', fontsize=9)

plt.tight_layout()
output_file = os.path.join(OUTPUT_DIR, "confronto_inconvenience_barchart.png")
plt.savefig(output_file, dpi=300, bbox_inches='tight')
plt.close()
print(f"✅ Grafico inconvenience barre salvato: {output_file}")

# === 11. Grafico Vittorie Dettagliato ===
fig, ax = plt.subplots(figsize=(14, 10))

# Conta vittorie per ogni metrica
metriche = ['Inconvenience_Mean', 'Ave_Util_Mean', 'TSTT_Normalizzato', 'Ave_AumentoTTArco (%)']
ott_vittorie = []
bench_vittorie = []

for metrica in metriche:
    ott_win = 0
    bench_win = 0
    
    for trip_num in sorted(common_trip_numbers):
        ott_row = df_ott[df_ott['Trip_Number'] == trip_num]
        bench_row = df_bench[df_bench['Trip_Number'] == trip_num]
        
        if not ott_row.empty and not bench_row.empty:
            if metrica == 'TSTT_Normalizzato':
                ott_val = ott_row[metrica].iloc[0] if not pd.isna(ott_row[metrica].iloc[0]) else np.inf
                bench_val = bench_row[metrica].iloc[0] if not pd.isna(bench_row[metrica].iloc[0]) else np.inf
            else:
                ott_val = ott_row[metrica].iloc[0] if not pd.isna(ott_row[metrica].iloc[0]) else np.inf
                bench_val = bench_row[metrica].iloc[0] if not pd.isna(bench_row[metrica].iloc[0]) else np.inf
            
            # Per metriche "minore è meglio"
            if not np.isinf(ott_val) and not np.isinf(bench_val):
                if ott_val < bench_val:
                    ott_win += 1
                elif bench_val < ott_val:
                    bench_win += 1
    
    ott_vittorie.append(ott_win)
    bench_vittorie.append(bench_win)

# Grafico a barre
x = np.arange(len(metriche))
width = 0.35

bars1 = ax.bar(x - width/2, ott_vittorie, width, label='Ottimizzazione', color='blue', alpha=0.7)
bars2 = ax.bar(x + width/2, bench_vittorie, width, label='Benchmark', color='red', alpha=0.7)

ax.set_xlabel('Metriche', fontsize=12)
ax.set_ylabel('Numero di Vittorie', fontsize=12)
ax.set_title('Confronto Vittorie per Metrica', fontsize=14, pad=20)
ax.set_xticks(x)
ax.set_xticklabels(metriche, rotation=45, ha='right')
ax.legend(fontsize=12)
ax.grid(True, alpha=0.3)

plt.tight_layout()
output_file = os.path.join(OUTPUT_DIR, "vittorie_dettagliate.png")
plt.savefig(output_file, dpi=300, bbox_inches='tight')
plt.close()
print(f"✅ Grafico vittorie dettagliate salvato: {output_file}")







# Grafico a barre dei vincitori
methods = list(winners_count.keys())
counts = list(winners_count.values())

bars = plt.bar(methods, counts, color=['blue', 'red'], alpha=0.7)
plt.ylabel('Numero di Vittorie Metriche')
plt.title('Confronto Generale: Ottimizzazione vs Benchmark\n(Basi: Minore inconveniente, minore utilizzo, ecc.)')
plt.grid(True, alpha=0.3)

# Aggiungi valori sulle barre
for bar, count in zip(bars, counts):
    plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
             str(count), ha='center', va='bottom', fontsize=12)

plt.tight_layout()
output_file = os.path.join(OUTPUT_DIR, "confronto_vincitori.png")
plt.savefig(output_file, dpi=300, bbox_inches='tight')
plt.close()
print(f"✅ Grafico vincitori salvato: {output_file}")

print(f"\n🎉 GENERAZIONE COMPLETATA!")
print(f"📁 Grafici salvati in: {OUTPUT_DIR}")
print(f"\n📊 Sintesi risultati:")
print(f"   Ottimizzazione vincitrice in {winners_count['Ottimizzazione']} metriche")
print(f"   Benchmark vincitore in {winners_count['Benchmark']} metriche")

# === Stampa tabella per verifica ===
print(f"\n📋 Tabella comparativa generata:")
print(df_comparison.to_string(index=False))