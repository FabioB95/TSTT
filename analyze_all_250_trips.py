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
EXCEL_FILE = "solution_ITERATIVE_UE_dataset_medium_traffic_250.xlsx"
OUTPUT_DIR = "/mnt/user-data/outputs/ANALYSIS_250_TRIPS"
COLORS_PATHS = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A4C93', '#1982C4']

# Crea directory output se non esiste
import os
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(f"{OUTPUT_DIR}/individual_trips", exist_ok=True)
os.makedirs(f"{OUTPUT_DIR}/summary_stats", exist_ok=True)

print("="*80)
print("ANALISI COMPLETA - 250 TRIP")
print("="*80)

# ============================================================================
# 1. CARICA I DATI
# ============================================================================
print("\n📂 Caricamento dati dall'Excel...")

try:
    # Carica tutti i sheet
    summary_df = pd.read_excel(EXCEL_FILE, sheet_name='Summary')
    convergence_df = pd.read_excel(EXCEL_FILE, sheet_name='Convergence')
    arc_stats_df = pd.read_excel(EXCEL_FILE, sheet_name='Arc_Statistics')
    assignments_df = pd.read_excel(EXCEL_FILE, sheet_name='Assignments')
    
    print(f"✓ Summary: {len(summary_df)} metriche")
    print(f"✓ Convergence: {len(convergence_df)} iterazioni")
    print(f"✓ Arc Statistics: {len(arc_stats_df)} archi")
    print(f"✓ Assignments: {len(assignments_df)} righe di assegnamento")
    
except FileNotFoundError:
    print(f"❌ ERRORE: File {EXCEL_FILE} non trovato!")
    print("Per favore, metti il file nella directory corrente e riprova.")
    exit(1)

# ============================================================================
# 2. STATISTICHE GENERALI
# ============================================================================
print("\n📊 Calcolo statistiche generali...")

# Conta trip e paths
n_trips = assignments_df['Trip_ID'].nunique()
n_paths_per_trip = assignments_df.groupby('Trip_ID')['Path_ID'].nunique()
total_demand = assignments_df.groupby('Trip_ID')['Demand'].first().sum()
total_assignments = len(assignments_df)

print(f"\n📈 Statistiche Dataset:")
print(f"   - Numero di Trip: {n_trips}")
print(f"   - Percorsi per trip (media): {n_paths_per_trip.mean():.1f}")
print(f"   - Percorsi per trip (min-max): {n_paths_per_trip.min()}-{n_paths_per_trip.max()}")
print(f"   - Domanda totale: {total_demand:.0f} veicoli")
print(f"   - Righe di assegnamento: {total_assignments}")

# Slot analysis
min_slot = assignments_df['Departure_Slot'].min()
max_slot = assignments_df['Departure_Slot'].max()
print(f"   - Range slot: {min_slot} - {max_slot}")

# ============================================================================
# 3. CREA VISUALIZZAZIONE CONVERGENZA
# ============================================================================
print("\n📉 Creazione grafico convergenza...")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Plot 1: TSTT over iterations
ax1.plot(convergence_df['Iteration'], convergence_df['TSTT']/1e6, 
         marker='o', linewidth=3, markersize=10, color='#2E86AB')
ax1.set_xlabel('Iterazione', fontsize=12, fontweight='bold')
ax1.set_ylabel('TSTT (milioni di minuti)', fontsize=12, fontweight='bold')
ax1.set_title('Convergenza del Total System Travel Time', fontsize=14, fontweight='bold')
ax1.grid(True, alpha=0.3)
ax1.set_xticks(convergence_df['Iteration'])

# Annotate values
for i, row in convergence_df.iterrows():
    ax1.annotate(f"{row['TSTT']/1e6:.1f}M", 
                xy=(row['Iteration'], row['TSTT']/1e6),
                xytext=(0, 10), textcoords='offset points',
                ha='center', fontsize=10, fontweight='bold')

# Plot 2: Change percentage
ax2.bar(convergence_df['Iteration'][1:], convergence_df['Change_%'][1:], 
        color='#A23B72', alpha=0.8, edgecolor='black', linewidth=2)
ax2.set_xlabel('Iterazione', fontsize=12, fontweight='bold')
ax2.set_ylabel('Variazione TSTT (%)', fontsize=12, fontweight='bold')
ax2.set_title('Riduzione del TSTT ad Ogni Iterazione', fontsize=14, fontweight='bold')
ax2.grid(axis='y', alpha=0.3)
ax2.axhline(y=5, color='red', linestyle='--', linewidth=2, label='Soglia 5%')
ax2.legend(fontsize=10)

# Annotate bars
for i, row in convergence_df[1:].iterrows():
    ax2.text(row['Iteration'], row['Change_%'] + 1, f"{row['Change_%']:.1f}%",
            ha='center', fontsize=10, fontweight='bold')

plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/summary_stats/convergence_analysis.png", dpi=300, bbox_inches='tight')
plt.close()
print(f"✓ Salvato: convergence_analysis.png")

# ============================================================================
# 4. ANALISI DISTRIBUZIONE DOMANDA PER TRIP
# ============================================================================
print("\n📊 Analisi distribuzione domanda...")

trip_demands = assignments_df.groupby('Trip_ID')['Demand'].first().sort_values(ascending=False)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# Histogram
ax1.hist(trip_demands, bins=50, color='#2E86AB', alpha=0.7, edgecolor='black')
ax1.set_xlabel('Domanda (veicoli)', fontsize=12, fontweight='bold')
ax1.set_ylabel('Numero di Trip', fontsize=12, fontweight='bold')
ax1.set_title('Distribuzione della Domanda per Trip', fontsize=14, fontweight='bold')
ax1.grid(axis='y', alpha=0.3)
ax1.axvline(trip_demands.mean(), color='red', linestyle='--', linewidth=2, 
           label=f'Media: {trip_demands.mean():.0f}')
ax1.axvline(trip_demands.median(), color='green', linestyle='--', linewidth=2,
           label=f'Mediana: {trip_demands.median():.0f}')
ax1.legend(fontsize=11)

# Top 20 trips
top_20 = trip_demands.head(20)
ax2.barh(range(len(top_20)), top_20.values, color='#A23B72', alpha=0.8, edgecolor='black')
ax2.set_yticks(range(len(top_20)))
ax2.set_yticklabels([f"Trip {int(tid)}" for tid in top_20.index], fontsize=9)
ax2.set_xlabel('Domanda (veicoli)', fontsize=12, fontweight='bold')
ax2.set_title('Top 20 Trip per Domanda', fontsize=14, fontweight='bold')
ax2.grid(axis='x', alpha=0.3)
ax2.invert_yaxis()

plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/summary_stats/demand_distribution.png", dpi=300, bbox_inches='tight')
plt.close()
print(f"✓ Salvato: demand_distribution.png")

# ============================================================================
# 5. ANALISI CONGESTIONE MEDIA PER TRIP
# ============================================================================
print("\n🚦 Analisi livelli di congestione...")

trip_congestion = assignments_df.groupby('Trip_ID').agg({
    'Demand': 'first',
    'FreeFlow_Time_min': 'first',
    'TravelTime_PWL_min': 'mean',
    'Inconvenience_PWL': 'mean'
}).reset_index()

trip_congestion['Congestion_Factor'] = (trip_congestion['TravelTime_PWL_min'] / 
                                        trip_congestion['FreeFlow_Time_min'])

# Categorize congestion
trip_congestion['Congestion_Level'] = pd.cut(
    trip_congestion['Congestion_Factor'],
    bins=[0, 1.1, 1.3, 1.5, 2.0, 10],
    labels=['Bassa (<10%)', 'Moderata (10-30%)', 'Alta (30-50%)', 'Severa (50-100%)', 'Estrema (>100%)']
)

fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Plot 1: Scatter demand vs congestion
scatter = axes[0, 0].scatter(trip_congestion['Demand'], 
                            trip_congestion['Congestion_Factor'],
                            c=trip_congestion['Congestion_Factor'], 
                            cmap='RdYlGn_r', s=50, alpha=0.6, edgecolors='black')
axes[0, 0].set_xlabel('Domanda (veicoli)', fontsize=12, fontweight='bold')
axes[0, 0].set_ylabel('Fattore di Congestione', fontsize=12, fontweight='bold')
axes[0, 0].set_title('Domanda vs Congestione', fontsize=14, fontweight='bold')
axes[0, 0].axhline(y=1.0, color='green', linestyle='--', linewidth=2, label='Free-Flow')
axes[0, 0].grid(True, alpha=0.3)
axes[0, 0].legend()
plt.colorbar(scatter, ax=axes[0, 0], label='Fattore Congestione')

# Plot 2: Congestion levels distribution
congestion_counts = trip_congestion['Congestion_Level'].value_counts().sort_index()
colors_cong = ['#2ECC71', '#F39C12', '#E67E22', '#E74C3C', '#8E44AD']
axes[0, 1].bar(range(len(congestion_counts)), congestion_counts.values, 
              color=colors_cong[:len(congestion_counts)], alpha=0.8, edgecolor='black', linewidth=2)
axes[0, 1].set_xticks(range(len(congestion_counts)))
axes[0, 1].set_xticklabels(congestion_counts.index, rotation=45, ha='right', fontsize=10)
axes[0, 1].set_ylabel('Numero di Trip', fontsize=12, fontweight='bold')
axes[0, 1].set_title('Distribuzione Livelli di Congestione', fontsize=14, fontweight='bold')
axes[0, 1].grid(axis='y', alpha=0.3)

# Annotate bars
for i, v in enumerate(congestion_counts.values):
    axes[0, 1].text(i, v + 2, str(v), ha='center', fontsize=11, fontweight='bold')

# Plot 3: Histogram of congestion factors
axes[1, 0].hist(trip_congestion['Congestion_Factor'], bins=50, 
               color='#3498DB', alpha=0.7, edgecolor='black')
axes[1, 0].set_xlabel('Fattore di Congestione', fontsize=12, fontweight='bold')
axes[1, 0].set_ylabel('Numero di Trip', fontsize=12, fontweight='bold')
axes[1, 0].set_title('Distribuzione Fattore di Congestione', fontsize=14, fontweight='bold')
axes[1, 0].axvline(trip_congestion['Congestion_Factor'].mean(), 
                  color='red', linestyle='--', linewidth=2,
                  label=f"Media: {trip_congestion['Congestion_Factor'].mean():.2f}x")
axes[1, 0].grid(axis='y', alpha=0.3)
axes[1, 0].legend(fontsize=11)

# Plot 4: Top 20 most congested trips
top_congested = trip_congestion.nlargest(20, 'Congestion_Factor')
axes[1, 1].barh(range(len(top_congested)), top_congested['Congestion_Factor'].values,
               color='#E74C3C', alpha=0.8, edgecolor='black')
axes[1, 1].set_yticks(range(len(top_congested)))
axes[1, 1].set_yticklabels([f"Trip {int(tid)}" for tid in top_congested['Trip_ID']], fontsize=9)
axes[1, 1].set_xlabel('Fattore di Congestione', fontsize=12, fontweight='bold')
axes[1, 1].set_title('Top 20 Trip Più Congestionati', fontsize=14, fontweight='bold')
axes[1, 1].axvline(x=1.0, color='green', linestyle='--', linewidth=2, label='Free-Flow')
axes[1, 1].grid(axis='x', alpha=0.3)
axes[1, 1].invert_yaxis()
axes[1, 1].legend()

plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/summary_stats/congestion_analysis.png", dpi=300, bbox_inches='tight')
plt.close()
print(f"✓ Salvato: congestion_analysis.png")

# ============================================================================
# 6. ANALISI TEMPORALE AGGREGATA
# ============================================================================
print("\n⏰ Analisi distribuzione temporale...")

# Aggregate vehicles by slot across all trips
slot_distribution = assignments_df.groupby('Departure_Slot')['Vehicles_Assigned'].sum()

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10))

# Plot 1: Total vehicles by slot
ax1.fill_between(slot_distribution.index, slot_distribution.values, 
                alpha=0.7, color='#2E86AB', edgecolor='black', linewidth=2)
ax1.set_xlabel('Slot di Partenza', fontsize=12, fontweight='bold')
ax1.set_ylabel('Veicoli Totali Assegnati', fontsize=12, fontweight='bold')
ax1.set_title('Distribuzione Temporale Totale - Tutti i Trip', fontsize=14, fontweight='bold')
ax1.grid(True, alpha=0.3)
ax1.axvline(x=108, color='red', linestyle='--', linewidth=3, label='Slot Limite (108)')
ax1.legend(fontsize=11)

# Highlight peak hours
peak_slots = slot_distribution.nlargest(10)
for slot in peak_slots.index:
    ax1.axvspan(slot-0.5, slot+0.5, alpha=0.2, color='red')

# Plot 2: Number of active trips per slot
trips_per_slot = assignments_df[assignments_df['Vehicles_Assigned'] > 0].groupby('Departure_Slot')['Trip_ID'].nunique()
ax2.bar(trips_per_slot.index, trips_per_slot.values, 
       color='#A23B72', alpha=0.8, edgecolor='black', linewidth=1)
ax2.set_xlabel('Slot di Partenza', fontsize=12, fontweight='bold')
ax2.set_ylabel('Numero di Trip Attivi', fontsize=12, fontweight='bold')
ax2.set_title('Numero di Trip Attivi per Slot', fontsize=14, fontweight='bold')
ax2.grid(axis='y', alpha=0.3)
ax2.axvline(x=108, color='red', linestyle='--', linewidth=3, label='Slot Limite')
ax2.legend(fontsize=11)

plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/summary_stats/temporal_distribution_aggregate.png", dpi=300, bbox_inches='tight')
plt.close()
print(f"✓ Salvato: temporal_distribution_aggregate.png")

# ============================================================================
# 7. GENERA GRAFICI INDIVIDUALI PER OGNI TRIP (250 trip)
# ============================================================================
print(f"\n🎨 Generazione grafici individuali per {n_trips} trip...")
print("   (Questo potrebbe richiedere qualche minuto...)")

trip_ids = sorted(assignments_df['Trip_ID'].unique())

for idx, trip_id in enumerate(trip_ids):
    if (idx + 1) % 50 == 0:
        print(f"   Progresso: {idx+1}/{n_trips} trip completati...")
    
    trip_data = assignments_df[assignments_df['Trip_ID'] == trip_id].copy()
    paths = sorted(trip_data['Path_ID'].unique())
    demand = trip_data['Demand'].iloc[0]
    
    # Skip if no data
    if len(trip_data) == 0:
        continue
    
    # Create figure
    fig = plt.figure(figsize=(16, 10))
    gs = GridSpec(3, 2, figure=fig, hspace=0.35, wspace=0.3)
    
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
    
    ax1.set_title(f'Trip {int(trip_id)}: Distribuzione Veicoli nel Tempo (Domanda: {demand:.0f})',
                 fontsize=13, fontweight='bold')
    ax1.set_xlabel('Slot di Partenza', fontsize=11)
    ax1.set_ylabel('Veicoli Assegnati', fontsize=11)
    ax1.legend(loc='upper left', fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.axvline(x=108, color='red', linestyle='--', linewidth=2, alpha=0.7, label='Limite Slot')
    
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
    # Plot 5: Summary Statistics
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
    plt.savefig(f"{OUTPUT_DIR}/individual_trips/trip_{int(trip_id):03d}.png",
               dpi=200, bbox_inches='tight')
    plt.close()

print(f"✓ Completati tutti i {n_trips} grafici individuali!")

# ============================================================================
# 8. CREA SUMMARY REPORT
# ============================================================================
print("\n📝 Creazione report riassuntivo...")

summary_report = f"""
================================================================================
REPORT ANALISI TEMPORALE - 250 TRIP
================================================================================

DATI GENERALI:
- Numero di Trip: {n_trips}
- Domanda Totale: {total_demand:.0f} veicoli
- Range Slot: {min_slot} - {max_slot}
- Righe di Assegnamento: {total_assignments}

CONVERGENZA:
- Iterazioni: {len(convergence_df)}
- TSTT Iniziale: {convergence_df.iloc[0]['TSTT']/1e6:.2f} M min
- TSTT Finale: {convergence_df.iloc[-1]['TSTT']/1e6:.2f} M min
- Riduzione Totale: {((convergence_df.iloc[0]['TSTT'] - convergence_df.iloc[-1]['TSTT'])/convergence_df.iloc[0]['TSTT']*100):.1f}%

DISTRIBUZIONE DOMANDA:
- Media: {trip_demands.mean():.1f} veicoli/trip
- Mediana: {trip_demands.median():.1f} veicoli/trip
- Min-Max: {trip_demands.min():.0f} - {trip_demands.max():.0f} veicoli

PERCORSI:
- Percorsi per trip (media): {n_paths_per_trip.mean():.1f}
- Percorsi per trip (range): {n_paths_per_trip.min()}-{n_paths_per_trip.max()}

CONGESTIONE:
- Fattore medio: {trip_congestion['Congestion_Factor'].mean():.2f}x
- Trips con congestione bassa: {len(trip_congestion[trip_congestion['Congestion_Factor'] < 1.1])}
- Trips con congestione moderata: {len(trip_congestion[(trip_congestion['Congestion_Factor'] >= 1.1) & (trip_congestion['Congestion_Factor'] < 1.3)])}
- Trips con congestione alta: {len(trip_congestion[(trip_congestion['Congestion_Factor'] >= 1.3) & (trip_congestion['Congestion_Factor'] < 1.5)])}
- Trips con congestione severa: {len(trip_congestion[trip_congestion['Congestion_Factor'] >= 1.5])}

ARCHI:
- Numero di archi: {len(arc_stats_df)}
- Utilizzo medio: {arc_stats_df['Ave_Ave_Util'].mean():.1f}%
- Utilizzo massimo: {arc_stats_df['Max_Max_Util'].max():.1f}%

FILE GENERATI:
- Grafici individuali: {n_trips} file in individual_trips/
- Statistiche aggregate: 4 file in summary_stats/

================================================================================
"""

with open(f"{OUTPUT_DIR}/SUMMARY_REPORT.txt", "w") as f:
    f.write(summary_report)

print(summary_report)

print("\n" + "="*80)
print("✅ ANALISI COMPLETATA CON SUCCESSO!")
print("="*80)
print(f"\nTutti i file sono stati salvati in: {OUTPUT_DIR}")
print("\nProssimo step: Esegui app_interactive.py per l'interfaccia interattiva!")