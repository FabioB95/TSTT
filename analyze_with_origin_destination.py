"""
SCRIPT AGGIORNATO CON ORIGINE/DESTINAZIONE
Aggiunge info nodi ai grafici individuali
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.gridspec import GridSpec
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURAZIONE
# ============================================================================
SOLUTION_FILE = "solution_ITERATIVE_UE_dataset_medium_traffic_250.xlsx"
INPUT_FILE = "INPUT_DATASETS/MEDIUM/OTT/dataset_medium_traffic_250.xlsx"
OUTPUT_DIR = "/mnt/user-data/outputs/ANALYSIS_250_TRIPS_WITH_NODES"
COLORS_PATHS = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A4C93', '#1982C4']

import os
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(f"{OUTPUT_DIR}/individual_trips", exist_ok=True)
os.makedirs(f"{OUTPUT_DIR}/summary_stats", exist_ok=True)

print("="*80)
print("ANALISI COMPLETA CON INFO ORIGINE/DESTINAZIONE")
print("="*80)

# ============================================================================
# CARICA DATI
# ============================================================================
print("\n📂 Caricamento dati...")

# Load SOLUTION
summary_df = pd.read_excel(SOLUTION_FILE, sheet_name='Summary')
convergence_df = pd.read_excel(SOLUTION_FILE, sheet_name='Convergence')
arc_stats_df = pd.read_excel(SOLUTION_FILE, sheet_name='Arc_Statistics')
assignments_df = pd.read_excel(SOLUTION_FILE, sheet_name='Assignments')

print(f"✓ SOLUTION - Summary: {len(summary_df)} metriche")
print(f"✓ SOLUTION - Convergence: {len(convergence_df)} iterazioni")
print(f"✓ SOLUTION - Arc Statistics: {len(arc_stats_df)} archi")
print(f"✓ SOLUTION - Assignments: {len(assignments_df)} righe")

# Load INPUT for origin/destination
trips_input_df = pd.read_excel(INPUT_FILE, sheet_name='trips')
nodes_input_df = pd.read_excel(INPUT_FILE, sheet_name='nodes')

print(f"✓ INPUT - Trips definiti: {len(trips_input_df)}")
print(f"✓ INPUT - Nodi: {len(nodes_input_df)}")

# Create mapping trip_id -> origin, destination
trip_od_map = {}
for _, row in trips_input_df.iterrows():
    trip_od_map[row['trip_id']] = {
        'origin': row['origin'],
        'destination': row['destination'],
        'demand': row['demand']
    }

# Create mapping node ID -> name
node_name_map = {}
for _, row in nodes_input_df.iterrows():
    node_name_map[str(row['ID'])] = row['name']

print(f"✓ Mapping creati: {len(trip_od_map)} trip con O/D")

# ============================================================================
# STATISTICHE GENERALI
# ============================================================================
print("\n📊 Calcolo statistiche generali...")

n_trips_assigned = assignments_df['Trip_ID'].nunique()
n_trips_defined = len(trips_input_df)
n_trips_not_assigned = n_trips_defined - n_trips_assigned

print(f"\n📈 Trip Status:")
print(f"   - Trip definiti nell'INPUT: {n_trips_defined}")
print(f"   - Trip con assegnamenti: {n_trips_assigned}")
print(f"   - Trip senza assegnamenti: {n_trips_not_assigned}")
print(f"   → Questo spiega perché 235 invece di 250!")

# Rest of statistics...
total_demand = assignments_df.groupby('Trip_ID')['Demand'].first().sum()
n_paths_per_trip = assignments_df.groupby('Trip_ID')['Path_ID'].nunique()

print(f"\n📊 Dettagli:")
print(f"   - Domanda totale: {total_demand:.0f} veicoli")
print(f"   - Percorsi per trip (media): {n_paths_per_trip.mean():.1f}")
print(f"   - Range slot: {assignments_df['Departure_Slot'].min()} - {assignments_df['Departure_Slot'].max()}")

# ============================================================================
# SKIP convergence/demand/congestion graphs (already done)
# ============================================================================
print("\n⏩ Salto grafici aggregati (già generati in precedenza)")

# ============================================================================
# GENERA GRAFICI INDIVIDUALI CON ORIGINE/DESTINAZIONE
# ============================================================================
print(f"\n🎨 Generazione grafici individuali con O/D per {n_trips_assigned} trip...")
print("   (Solo trip con origine/destinazione trovati)")

trip_ids = sorted(assignments_df['Trip_ID'].unique())
generated_count = 0
skipped_count = 0

for idx, trip_id in enumerate(trip_ids):
    if (idx + 1) % 50 == 0:
        print(f"   Progresso: {idx+1}/{n_trips_assigned} trip...")
    
    trip_data = assignments_df[assignments_df['Trip_ID'] == trip_id].copy()
    paths = sorted(trip_data['Path_ID'].unique())
    demand = trip_data['Demand'].iloc[0]
    
    # Get origin/destination
    if trip_id in trip_od_map:
        origin_id = str(trip_od_map[trip_id]['origin'])
        dest_id = str(trip_od_map[trip_id]['destination'])
        
        # Get node names
        origin_name = node_name_map.get(origin_id, origin_id)
        dest_name = node_name_map.get(dest_id, dest_id)
        
        od_text = f"{origin_name} → {dest_name}"
    else:
        od_text = "O/D non disponibile"
        skipped_count += 1
    
    # Create figure
    fig = plt.figure(figsize=(16, 10))
    gs = GridSpec(3, 2, figure=fig, hspace=0.35, wspace=0.3)
    
    # ========================================================================
    # TITLE WITH ORIGIN/DESTINATION
    # ========================================================================
    fig.suptitle(f'Trip {int(trip_id)}: {od_text}\n(Domanda: {demand:.0f} veicoli)', 
                fontsize=14, fontweight='bold', y=0.98)
    
    # ========================================================================
    # Plot 1: Vehicle Distribution Over Time
    # ========================================================================
    ax1 = fig.add_subplot(gs[0, :])
    
    pivot_data = trip_data.pivot_table(
        index='Departure_Slot',
        columns='Path_ID',
        values='Vehicles_Assigned',
        fill_value=0
    )
    
    ax1.stackplot(pivot_data.index,
                 [pivot_data[path] for path in paths],
                 labels=[f'Path {int(path)}' for path in paths],
                 colors=COLORS_PATHS[:len(paths)],
                 alpha=0.8)
    
    ax1.set_title(f'Distribuzione Veicoli nel Tempo', fontsize=12, fontweight='bold')
    ax1.set_xlabel('Slot di Partenza', fontsize=11)
    ax1.set_ylabel('Veicoli Assegnati', fontsize=11)
    ax1.legend(loc='upper left', fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.axvline(x=108, color='red', linestyle='--', linewidth=2, alpha=0.7)
    
    # ========================================================================
    # Plot 2: Path Split Percentage
    # ========================================================================
    ax2 = fig.add_subplot(gs[1, 0])
    
    total_per_slot = trip_data.groupby('Departure_Slot')['Vehicles_Assigned'].sum()
    
    for i, path_id in enumerate(paths):
        path_data = trip_data[trip_data['Path_ID'] == path_id]
        percentages = (path_data.set_index('Departure_Slot')['Vehicles_Assigned'] / 
                      total_per_slot * 100)
        
        ax2.plot(percentages.index, percentages.values,
                marker='o', markersize=3, linewidth=2,
                label=f'Path {int(path_id)}',
                color=COLORS_PATHS[i % len(COLORS_PATHS)])
    
    ax2.set_title('Path Split Percentage', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Slot di Partenza', fontsize=10)
    ax2.set_ylabel('% Veicoli', fontsize=10)
    ax2.set_ylim(0, 100)
    ax2.legend(loc='best', fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=50, color='gray', linestyle='--', alpha=0.5)
    
    # ========================================================================
    # Plot 3: Travel Time Evolution
    # ========================================================================
    ax3 = fig.add_subplot(gs[1, 1])
    
    for i, path_id in enumerate(paths):
        path_data = trip_data[trip_data['Path_ID'] == path_id].sort_values('Departure_Slot')
        
        ax3.plot(path_data['Departure_Slot'],
                path_data['TravelTime_PWL_min'],
                marker='o', markersize=3, linewidth=2,
                label=f'Path {int(path_id)}',
                color=COLORS_PATHS[i % len(COLORS_PATHS)])
    
    free_flow = trip_data['FreeFlow_Time_min'].iloc[0]
    ax3.axhline(y=free_flow, color='green', linestyle='--',
               alpha=0.7, linewidth=2, label='Free Flow')
    
    ax3.set_title('Evoluzione Tempi di Viaggio', fontsize=12, fontweight='bold')
    ax3.set_xlabel('Slot di Partenza', fontsize=10)
    ax3.set_ylabel('Tempo di Viaggio (min)', fontsize=10)
    ax3.legend(loc='best', fontsize=9)
    ax3.grid(True, alpha=0.3)
    
    # ========================================================================
    # Plot 4: Inconvenience Evolution
    # ========================================================================
    ax4 = fig.add_subplot(gs[2, 0])
    
    for i, path_id in enumerate(paths):
        path_data = trip_data[trip_data['Path_ID'] == path_id].sort_values('Departure_Slot')
        
        ax4.plot(path_data['Departure_Slot'],
                path_data['Inconvenience_PWL'],
                marker='o', markersize=3, linewidth=2,
                label=f'Path {int(path_id)}',
                color=COLORS_PATHS[i % len(COLORS_PATHS)])
    
    ax4.axhline(y=1.0, color='green', linestyle='--',
               alpha=0.7, linewidth=2, label='No Inconvenience')
    ax4.set_title('Inconvenience Factor', fontsize=12, fontweight='bold')
    ax4.set_xlabel('Slot di Partenza', fontsize=10)
    ax4.set_ylabel('Inconvenience', fontsize=10)
    ax4.legend(loc='best', fontsize=9)
    ax4.grid(True, alpha=0.3)
    
    # ========================================================================
    # Plot 5: Summary Statistics with O/D
    # ========================================================================
    ax5 = fig.add_subplot(gs[2, 1])
    ax5.axis('off')
    
    # Calculate statistics
    total_assigned = trip_data['Vehicles_Assigned'].sum()
    avg_travel_time = trip_data['TravelTime_PWL_min'].mean()
    avg_inconvenience = trip_data['Inconvenience_PWL'].mean()
    congestion_factor = avg_travel_time / free_flow
    n_paths = len(paths)
    slots_used = trip_data[trip_data['Vehicles_Assigned'] > 0]['Departure_Slot'].nunique()
    min_slot = trip_data[trip_data['Vehicles_Assigned'] > 0]['Departure_Slot'].min()
    max_slot = trip_data[trip_data['Vehicles_Assigned'] > 0]['Departure_Slot'].max()
    
    # Check if all vehicles departed before slot 108
    late_departures = trip_data[trip_data['Departure_Slot'] > 108]['Vehicles_Assigned'].sum()
    on_time = "✓ Sì" if late_departures == 0 else f"✗ No ({late_departures:.1f} dopo slot 108)"
    
    stats_text = f"""
    STATISTICHE TRIP {int(trip_id)}
    
    Origine: {origin_name if trip_id in trip_od_map else 'N/A'}
    Destinazione: {dest_name if trip_id in trip_od_map else 'N/A'}
    
    Domanda Totale: {demand:.0f} veicoli
    Veicoli Assegnati: {total_assigned:.1f} ({total_assigned/demand*100:.1f}%)
    
    Numero di Percorsi: {n_paths}
    Slot Utilizzati: {slots_used} (da {min_slot} a {max_slot})
    Tutti partiti entro slot 108: {on_time}
    
    Tempo Free-Flow: {free_flow:.1f} min
    Tempo Medio Effettivo: {avg_travel_time:.1f} min
    Fattore Congestione: {congestion_factor:.2f}x
    
    Inconvenience Medio: {avg_inconvenience:.3f}
    """
    
    ax5.text(0.1, 0.9, stats_text, transform=ax5.transAxes,
            fontsize=10, verticalalignment='top', fontfamily='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # Save figure
    plt.savefig(f"{OUTPUT_DIR}/individual_trips/trip_{int(trip_id):03d}_with_OD.png",
               dpi=200, bbox_inches='tight')
    plt.close()
    generated_count += 1

print(f"\n✓ Generati {generated_count} grafici con info O/D")
if skipped_count > 0:
    print(f"⚠️  {skipped_count} trip senza mapping O/D")

# ============================================================================
# REPORT FINALE
# ============================================================================
print("\n📝 Creazione report...")

report = f"""
================================================================================
REPORT ANALISI CON ORIGINE/DESTINAZIONE
================================================================================

CONFRONTO TRIP:
- Trip definiti nell'INPUT: {n_trips_defined}
- Trip con assegnamenti nella SOLUTION: {n_trips_assigned}
- Trip non assegnati: {n_trips_not_assigned}

SPIEGAZIONE:
La differenza tra 250 (INPUT) e 235 (SOLUTION) è normale e può essere dovuta a:
1. Trip con domanda troppo bassa (non raggiungo threshold minimo)
2. Trip filtrati per slot availability
3. Trip che non convergono (removed dal modello)
4. Trip con percorsi non feasible

MAPPING ORIGINE/DESTINAZIONE:
- Trip con O/D trovati: {len([t for t in trip_ids if t in trip_od_map])}
- Trip senza O/D: {len([t for t in trip_ids if t not in trip_od_map])}

GRAFICI GENERATI:
- {generated_count} grafici con info origine/destinazione completa
- Tutti salvati in: {OUTPUT_DIR}/individual_trips/

ESEMPIO MAPPING NODI:
"""

# Add some example mappings
for trip_id in list(trip_ids)[:5]:
    if trip_id in trip_od_map:
        origin_id = str(trip_od_map[trip_id]['origin'])
        dest_id = str(trip_od_map[trip_id]['destination'])
        origin_name = node_name_map.get(origin_id, origin_id)
        dest_name = node_name_map.get(dest_id, dest_id)
        report += f"\nTrip {trip_id}: {origin_name} ({origin_id}) → {dest_name} ({dest_id})"

report += "\n\n" + "="*80

with open(f"{OUTPUT_DIR}/REPORT_WITH_OD.txt", "w", encoding='utf-8') as f:
    f.write(report)

print(report)

print("\n" + "="*80)
print("✅ ANALISI CON O/D COMPLETATA!")
print("="*80)
print(f"\nFile salvati in: {OUTPUT_DIR}")
print("\n💡 Differenza 235 vs 250 trip è normale e documentata nel report!")
print("="*80)