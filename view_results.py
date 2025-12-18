"""
VISUALIZZATORE RISULTATI SEMPLICE (senza Streamlit)
Mostra i risultati chiave dell'analisi in modo testuale
"""

import pandas as pd
import os

print("="*80)
print("📊 VISUALIZZATORE RISULTATI - ANALISI 250 TRIP")
print("="*80)

# ============================================================================
# CARICA DATI
# ============================================================================
print("\n📂 Caricamento dati...")

EXCEL_FILE = "solution_ITERATIVE_UE_dataset_medium_traffic_250.xlsx"

try:
    summary_df = pd.read_excel(EXCEL_FILE, sheet_name='Summary')
    convergence_df = pd.read_excel(EXCEL_FILE, sheet_name='Convergence')
    arc_stats_df = pd.read_excel(EXCEL_FILE, sheet_name='Arc_Statistics')
    assignments_df = pd.read_excel(EXCEL_FILE, sheet_name='Assignments')
    print("✓ Dati caricati con successo")
except Exception as e:
    print(f"❌ Errore caricamento: {e}")
    exit(1)

# ============================================================================
# STATISTICHE GENERALI
# ============================================================================
print("\n" + "="*80)
print("📈 STATISTICHE GENERALI")
print("="*80)

n_trips = assignments_df['Trip_ID'].nunique()
total_demand = assignments_df.groupby('Trip_ID')['Demand'].first().sum()
total_assigned = assignments_df['Vehicles_Assigned'].sum()

print(f"\n🚗 TRIP E DOMANDA:")
print(f"   Numero di Trip: {n_trips}")
print(f"   Domanda Totale: {total_demand:,.0f} veicoli")
print(f"   Veicoli Assegnati: {total_assigned:,.1f}")
print(f"   Tasso Assegnamento: {(total_assigned/total_demand*100):.1f}%")

# ============================================================================
# CONVERGENZA
# ============================================================================
print("\n" + "="*80)
print("📉 CONVERGENZA")
print("="*80)

print(f"\n🔄 ITERAZIONI: {len(convergence_df)}")
print("\n   Iter | TSTT (M min) | Riduzione %")
print("   " + "-"*40)
for _, row in convergence_df.iterrows():
    iter_num = int(row['Iteration'])
    tstt = row['TSTT'] / 1e6
    change = row['Change_%']
    if iter_num == 1:
        print(f"   {iter_num:4d} | {tstt:12.2f} |     -")
    else:
        print(f"   {iter_num:4d} | {tstt:12.2f} | {change:10.1f}%")

reduction = (convergence_df.iloc[0]['TSTT'] - convergence_df.iloc[-1]['TSTT']) / convergence_df.iloc[0]['TSTT'] * 100
print(f"\n✅ Riduzione TSTT totale: {reduction:.1f}%")

# ============================================================================
# DISTRIBUZIONE DOMANDA
# ============================================================================
print("\n" + "="*80)
print("📊 DISTRIBUZIONE DOMANDA")
print("="*80)

trip_demands = assignments_df.groupby('Trip_ID')['Demand'].first()

print(f"\n   Media: {trip_demands.mean():,.0f} veicoli/trip")
print(f"   Mediana: {trip_demands.median():,.0f} veicoli/trip")
print(f"   Min: {trip_demands.min():,.0f} veicoli")
print(f"   Max: {trip_demands.max():,.0f} veicoli")
print(f"   Deviazione Standard: {trip_demands.std():,.0f}")

# Top 10 trip per domanda
print(f"\n📌 TOP 10 TRIP PER DOMANDA:")
top_10 = trip_demands.nlargest(10)
for rank, (trip_id, demand) in enumerate(top_10.items(), 1):
    print(f"   {rank:2d}. Trip {int(trip_id):3d}: {demand:6,.0f} veicoli")

# ============================================================================
# CONGESTIONE
# ============================================================================
print("\n" + "="*80)
print("🚦 ANALISI CONGESTIONE")
print("="*80)

trip_congestion = assignments_df.groupby('Trip_ID').agg({
    'Demand': 'first',
    'FreeFlow_Time_min': 'first',
    'TravelTime_PWL_min': 'mean'
}).reset_index()

trip_congestion['Congestion_Factor'] = (trip_congestion['TravelTime_PWL_min'] / 
                                        trip_congestion['FreeFlow_Time_min'])

print(f"\n📈 FATTORE DI CONGESTIONE:")
print(f"   Media: {trip_congestion['Congestion_Factor'].mean():.2f}x")
print(f"   Mediana: {trip_congestion['Congestion_Factor'].median():.2f}x")
print(f"   Min: {trip_congestion['Congestion_Factor'].min():.2f}x")
print(f"   Max: {trip_congestion['Congestion_Factor'].max():.2f}x")

# Classificazione
low = len(trip_congestion[trip_congestion['Congestion_Factor'] < 1.1])
moderate = len(trip_congestion[(trip_congestion['Congestion_Factor'] >= 1.1) & 
                               (trip_congestion['Congestion_Factor'] < 1.3)])
high = len(trip_congestion[(trip_congestion['Congestion_Factor'] >= 1.3) & 
                           (trip_congestion['Congestion_Factor'] < 1.5)])
severe = len(trip_congestion[(trip_congestion['Congestion_Factor'] >= 1.5) & 
                             (trip_congestion['Congestion_Factor'] < 2.0)])
extreme = len(trip_congestion[trip_congestion['Congestion_Factor'] >= 2.0])

print(f"\n📊 CLASSIFICAZIONE TRIP:")
print(f"   Bassa (<10%): {low} trip ({low/n_trips*100:.1f}%)")
print(f"   Moderata (10-30%): {moderate} trip ({moderate/n_trips*100:.1f}%)")
print(f"   Alta (30-50%): {high} trip ({high/n_trips*100:.1f}%)")
print(f"   Severa (50-100%): {severe} trip ({severe/n_trips*100:.1f}%)")
print(f"   Estrema (>100%): {extreme} trip ({extreme/n_trips*100:.1f}%)")

# Top 10 più congestionati
print(f"\n🔴 TOP 10 TRIP PIÙ CONGESTIONATI:")
top_congested = trip_congestion.nlargest(10, 'Congestion_Factor')
for rank, (_, row) in enumerate(top_congested.iterrows(), 1):
    print(f"   {rank:2d}. Trip {int(row['Trip_ID']):3d}: {row['Congestion_Factor']:.2f}x " +
          f"(Free-flow: {row['FreeFlow_Time_min']:.0f} min → Effettivo: {row['TravelTime_PWL_min']:.0f} min)")

# ============================================================================
# UTILIZZO ARCHI
# ============================================================================
print("\n" + "="*80)
print("🛣️  UTILIZZO ARCHI")
print("="*80)

print(f"\n📊 STATISTICHE ARCHI:")
print(f"   Numero di archi: {len(arc_stats_df)}")
print(f"   Utilizzo medio: {arc_stats_df['Ave_Ave_Util'].mean():.1f}%")
print(f"   Utilizzo massimo osservato: {arc_stats_df['Max_Max_Util'].max():.1f}%")

# Archi più utilizzati
print(f"\n🔴 TOP 10 ARCHI PIÙ UTILIZZATI:")
top_arcs = arc_stats_df.nlargest(10, 'Ave_Ave_Util')
for rank, (_, row) in enumerate(top_arcs.iterrows(), 1):
    print(f"   {rank:2d}. Arco {row['From']} → {row['To']}: " +
          f"Utilizzo medio {row['Ave_Ave_Util']:.1f}%, Max {row['Max_Max_Util']:.1f}%")

# Archi over-capacity
over_capacity = arc_stats_df[arc_stats_df['Max_Max_Util'] > 100]
print(f"\n⚠️  ARCHI OVER-CAPACITY (>100%): {len(over_capacity)}")
if len(over_capacity) > 0:
    for _, row in over_capacity.head(10).iterrows():
        print(f"   • Arco {row['From']} → {row['To']}: {row['Max_Max_Util']:.1f}%")

# ============================================================================
# DISTRIBUZIONE TEMPORALE
# ============================================================================
print("\n" + "="*80)
print("⏰ DISTRIBUZIONE TEMPORALE")
print("="*80)

min_slot = assignments_df['Departure_Slot'].min()
max_slot = assignments_df['Departure_Slot'].max()
slots_used = assignments_df['Departure_Slot'].nunique()

print(f"\n📅 RANGE SLOT:")
print(f"   Slot minimo: {min_slot}")
print(f"   Slot massimo: {max_slot}")
print(f"   Slot utilizzati: {slots_used}")
print(f"   Range: {max_slot - min_slot + 1}")

# Slot con più veicoli
slot_distribution = assignments_df.groupby('Departure_Slot')['Vehicles_Assigned'].sum()
top_slots = slot_distribution.nlargest(10)

print(f"\n📈 TOP 10 SLOT PER VEICOLI ASSEGNATI:")
for rank, (slot, vehicles) in enumerate(top_slots.items(), 1):
    print(f"   {rank:2d}. Slot {int(slot):3d}: {vehicles:,.1f} veicoli")

# ============================================================================
# FILE GENERATI
# ============================================================================
print("\n" + "="*80)
print("📁 FILE GENERATI")
print("="*80)

output_dirs = [
    "/mnt/user-data/outputs/ANALYSIS_250_TRIPS",
    "/mnt/user-data/outputs/NETWORK_ANALYSIS_COMPLETE"
]

for output_dir in output_dirs:
    if os.path.exists(output_dir):
        print(f"\n✓ {output_dir}")
        
        # Count files
        summary_stats = os.path.join(output_dir, "summary_stats")
        individual_trips = os.path.join(output_dir, "individual_trips")
        individual_paths = os.path.join(output_dir, "individual_paths")
        
        if os.path.exists(summary_stats):
            n_files = len([f for f in os.listdir(summary_stats) if f.endswith('.png')])
            print(f"   - summary_stats/: {n_files} grafici")
        
        if os.path.exists(individual_trips):
            n_files = len([f for f in os.listdir(individual_trips) if f.endswith('.png')])
            print(f"   - individual_trips/: {n_files} grafici")
        
        if os.path.exists(individual_paths):
            n_files = len([f for f in os.listdir(individual_paths) if f.endswith('.png')])
            print(f"   - individual_paths/: {n_files} grafici")
        
        # Check for Excel files
        excel_files = [f for f in os.listdir(output_dir) if f.endswith('.xlsx')]
        if excel_files:
            print(f"   - Excel files: {len(excel_files)}")
            for excel_file in excel_files:
                print(f"      • {excel_file}")
    else:
        print(f"\n✗ {output_dir} - Non trovato")

# ============================================================================
# RIEPILOGO FINALE
# ============================================================================
print("\n" + "="*80)
print("🎯 RIEPILOGO FINALE")
print("="*80)

print(f"""
✅ RISULTATI CHIAVE:
   • {n_trips} trip analizzati ({total_demand:,.0f} veicoli)
   • Convergenza in {len(convergence_df)} iterazioni ({reduction:.1f}% riduzione TSTT)
   • Congestione media: {trip_congestion['Congestion_Factor'].mean():.2f}x
   • {severe + extreme} trip con congestione severa/estrema ({(severe+extreme)/n_trips*100:.1f}%)
   • {len(over_capacity)} archi over-capacity
   • Range temporale: slot {min_slot}-{max_slot}

💡 PROSSIMI PASSI:
   1. Rivedi i grafici generati in /mnt/user-data/outputs/
   2. Per analisi interattiva, installa Streamlit:
      pip install streamlit
      streamlit run app_interactive.py
   3. Per analisi percorsi, esegui:
      python complete_path_analysis.py

📖 Per maggiori dettagli, leggi il README:
   /mnt/user-data/outputs/README_ANALISI_250_TRIPS.md
""")

print("="*80)
print("✅ VISUALIZZAZIONE COMPLETATA")
print("="*80)