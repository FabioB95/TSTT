"""
VISUALIZZAZIONE COMPLETA PERCORSI CON ARCHI IN COMUNE
Usa il file INPUT per caricare la definizione dei percorsi reali
"""

import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURAZIONE
# ============================================================================
INPUT_FILE = "INPUT_DATASETS/MEDIUM/OTT/dataset_medium_traffic_250.xlsx"
SOLUTION_FILE = "solution_ITERATIVE_UE_dataset_medium_traffic_250.xlsx"
OUTPUT_DIR = "/mnt/user-data/outputs/NETWORK_ANALYSIS_COMPLETE"

import os
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(f"{OUTPUT_DIR}/individual_paths", exist_ok=True)

print("="*80)
print("ANALISI COMPLETA RETE E PERCORSI CON ARCHI IN COMUNE")
print("="*80)

# ============================================================================
# CARICA DATI
# ============================================================================
print("\n📂 Caricamento dati...")

# Load INPUT dataset
arcs_df = pd.read_excel(INPUT_FILE, sheet_name='arcs')
trips_df = pd.read_excel(INPUT_FILE, sheet_name='trips')
nodes_df = pd.read_excel(INPUT_FILE, sheet_name='nodes')

# Load SOLUTION
assignments_df = pd.read_excel(SOLUTION_FILE, sheet_name='Assignments')
arc_stats_df = pd.read_excel(SOLUTION_FILE, sheet_name='Arc_Statistics')

print(f"✓ INPUT - Arcs: {len(arcs_df)}")
print(f"✓ INPUT - Trips: {len(trips_df)}")
print(f"✓ INPUT - Nodes: {len(nodes_df)}")
print(f"✓ SOLUTION - Assignments: {len(assignments_df)}")

# ============================================================================
# PARSE PERCORSI DAI TRIP
# ============================================================================
print("\n🔍 Parsing percorsi dai trip...")

def parse_path_string(path_str):
    """
    Parse una stringa tipo '59_71,71_70,70_60,60_62'
    Ritorna lista di tuple (from, to)
    """
    if pd.isna(path_str) or path_str == '':
        return []
    
    arcs = path_str.split(',')
    parsed_arcs = []
    
    for arc in arcs:
        nodes = arc.split('_')
        if len(nodes) == 2:
            parsed_arcs.append((nodes[0], nodes[1]))
    
    return parsed_arcs

# Crea dizionario paths: trip_id -> path_id -> lista archi
paths_dict = defaultdict(dict)

for idx, row in trips_df.iterrows():
    trip_id = row['trip_id']
    
    # Parse path_0
    if 'path_0' in row and not pd.isna(row['path_0']):
        paths_dict[trip_id][0] = parse_path_string(row['path_0'])
    
    # Parse path_1
    if 'path_1' in row and not pd.isna(row['path_1']):
        paths_dict[trip_id][1] = parse_path_string(row['path_1'])
    
    # Parse path_2
    if 'path_2' in row and not pd.isna(row['path_2']):
        paths_dict[trip_id][2] = parse_path_string(row['path_2'])

n_trips_with_paths = len(paths_dict)
total_paths = sum(len(paths) for paths in paths_dict.values())

print(f"✓ Parsati {n_trips_with_paths} trip con percorsi")
print(f"✓ Totale percorsi: {total_paths}")

# Esempio di alcuni percorsi
print(f"\n📋 Esempio percorsi:")
for trip_id in list(paths_dict.keys())[:3]:
    print(f"   Trip {trip_id}:")
    for path_id, arcs in paths_dict[trip_id].items():
        print(f"      Path {path_id}: {len(arcs)} archi")

# ============================================================================
# CREA GRAFO DELLA RETE
# ============================================================================
print("\n🗺️  Costruzione grafo della rete...")

G = nx.DiGraph()

# Aggiungi nodi con attributi
for _, node in nodes_df.iterrows():
    G.add_node(str(node['ID']),
              name=node['name'],
              lat=node['lat'],
              lon=node['lon'],
              category=node.get('category', 'unknown'))

# Aggiungi archi con attributi
for _, arc in arcs_df.iterrows():
    from_node = str(arc['from_node'])
    to_node = str(arc['to_node'])
    
    G.add_edge(from_node, to_node,
              arc_id=arc['arc_id'],
              capacity=arc['capacity'],
              fftt=arc['fftt'])

print(f"✓ Grafo creato: {G.number_of_nodes()} nodi, {G.number_of_edges()} archi")

# ============================================================================
# TROVA ARCHI IN COMUNE TRA TRIP
# ============================================================================
print("\n🔍 Analisi archi in comune tra trip...")

def find_common_arcs_detailed(paths_dict):
    """
    Trova archi in comune tra trip diversi
    Ritorna dict: arc -> list of (trip_id, path_id)
    """
    arc_usage = defaultdict(list)
    
    for trip_id, paths in paths_dict.items():
        for path_id, arcs in paths.items():
            for arc in arcs:
                arc_usage[arc].append((trip_id, path_id))
    
    # Statistiche
    arc_stats = {}
    for arc, usage in arc_usage.items():
        unique_trips = set(t for t, p in usage)
        arc_stats[arc] = {
            'n_trips': len(unique_trips),
            'n_paths': len(usage),
            'trip_ids': sorted(unique_trips),
            'usage': usage
        }
    
    return arc_stats

arc_usage_stats = find_common_arcs_detailed(paths_dict)

# Archi più condivisi
shared_arcs = {arc: stats for arc, stats in arc_usage_stats.items() 
               if stats['n_trips'] > 1}

print(f"✓ Totale archi nella rete: {len(arc_usage_stats)}")
print(f"✓ Archi usati da più trip: {len(shared_arcs)}")

# Top 20 archi più condivisi
top_shared = sorted(shared_arcs.items(), 
                   key=lambda x: x[1]['n_trips'], 
                   reverse=True)[:20]

print(f"\n📊 Top 10 archi più condivisi:")
for i, (arc, stats) in enumerate(top_shared[:10], 1):
    print(f"   {i}. Arco {arc[0]}→{arc[1]}: usato da {stats['n_trips']} trip ({stats['n_paths']} path totali)")

# ============================================================================
# VISUALIZZA RETE COMPLETA CON ARCHI CONDIVISI
# ============================================================================
print("\n🎨 Creazione visualizzazione rete con archi condivisi...")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(24, 12))

# Layout usando coordinate geografiche
pos = {}
for node_id in G.nodes():
    node_data = nodes_df[nodes_df['ID'] == node_id]
    if len(node_data) > 0:
        # Usa lon, lat (invertiti per grafico)
        pos[node_id] = (node_data.iloc[0]['lon'], node_data.iloc[0]['lat'])
    else:
        # Fallback per nodi non trovati
        pos[node_id] = (0, 0)

# Plot 1: Rete colorata per numero di trip che usano ogni arco
ax1.set_title('Rete Completa - Archi Colorati per Numero di Trip che li Usano', 
             fontsize=16, fontweight='bold')

# Calcola colore per ogni arco
edge_colors = []
edge_widths = []
for u, v in G.edges():
    arc = (u, v)
    if arc in arc_usage_stats:
        n_trips = arc_usage_stats[arc]['n_trips']
        edge_colors.append(n_trips)
        edge_widths.append(1 + n_trips * 0.5)  # Width proporzionale
    else:
        edge_colors.append(0)
        edge_widths.append(0.5)

# Draw network
nx.draw_networkx_nodes(G, pos, ax=ax1, node_color='lightblue', 
                      node_size=400, edgecolors='black', linewidths=2, alpha=0.9)

edges = nx.draw_networkx_edges(G, pos, ax=ax1, 
                               edge_color=edge_colors,
                               edge_cmap=plt.cm.YlOrRd,
                               edge_vmin=0,
                               edge_vmax=max(edge_colors) if edge_colors else 10,
                               width=edge_widths,
                               arrows=True,
                               arrowsize=15,
                               connectionstyle='arc3,rad=0.05')

# Labels
nx.draw_networkx_labels(G, pos, ax=ax1, font_size=8, font_weight='bold')

# Colorbar
sm = plt.cm.ScalarMappable(cmap=plt.cm.YlOrRd,
                          norm=plt.Normalize(vmin=0, vmax=max(edge_colors) if edge_colors else 10))
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax1, fraction=0.046, pad=0.04)
cbar.set_label('Numero di Trip che Usano l\'Arco', fontsize=12, fontweight='bold')

ax1.axis('off')

# Plot 2: Evidenzia top 20 archi più condivisi
ax2.set_title('Top 20 Archi Più Condivisi (Evidenziati in Rosso)', 
             fontsize=16, fontweight='bold')

# Draw base network in gray
nx.draw_networkx_nodes(G, pos, ax=ax2, node_color='lightgray', 
                      node_size=400, edgecolors='black', linewidths=2, alpha=0.7)

nx.draw_networkx_edges(G, pos, ax=ax2, edge_color='lightgray',
                      width=1, alpha=0.3, arrows=True, arrowsize=10)

# Highlight top shared arcs
top_arcs = [arc for arc, _ in top_shared]
top_arcs_in_graph = [(u, v) for u, v in top_arcs if G.has_edge(u, v)]

if top_arcs_in_graph:
    nx.draw_networkx_edges(G, pos, edgelist=top_arcs_in_graph, ax=ax2,
                          edge_color='red', width=4, alpha=0.8,
                          arrows=True, arrowsize=20,
                          connectionstyle='arc3,rad=0.05')

nx.draw_networkx_labels(G, pos, ax=ax2, font_size=8, font_weight='bold')

# Add legend
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor='red', edgecolor='black', label=f'Top 20 archi più condivisi'),
    Patch(facecolor='lightgray', edgecolor='black', label='Altri archi')
]
ax2.legend(handles=legend_elements, loc='upper right', fontsize=11)

ax2.axis('off')

plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/network_with_shared_arcs.png", dpi=300, bbox_inches='tight')
plt.close()
print(f"✓ Salvato: network_with_shared_arcs.png")

# ============================================================================
# VISUALIZZA PERCORSI PER SINGOLI TRIP (Primi 10 come esempio)
# ============================================================================
print("\n🎨 Creazione visualizzazioni per singoli trip (esempio primi 10)...")

COLORS_PATHS = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A4C93', '#1982C4']

example_trips = list(paths_dict.keys())[:10]

for trip_id in example_trips:
    paths = paths_dict[trip_id]
    
    if len(paths) == 0:
        continue
    
    fig, ax = plt.subplots(figsize=(16, 12))
    
    # Draw base network in light gray
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color='white',
                          node_size=500, edgecolors='black', linewidths=2)
    
    nx.draw_networkx_edges(G, pos, ax=ax, edge_color='lightgray',
                          width=0.5, alpha=0.2, arrows=True, arrowsize=10)
    
    # Draw paths for this trip
    for path_id, arcs in paths.items():
        color = COLORS_PATHS[path_id % len(COLORS_PATHS)]
        
        # Filter arcs that exist in graph
        valid_arcs = [(u, v) for u, v in arcs if G.has_edge(u, v)]
        
        if valid_arcs:
            nx.draw_networkx_edges(G, pos, edgelist=valid_arcs, ax=ax,
                                  edge_color=color, width=4, alpha=0.8,
                                  arrows=True, arrowsize=20,
                                  connectionstyle='arc3,rad=0.1',
                                  label=f'Path {path_id} ({len(valid_arcs)} archi)')
    
    # Highlight nodes used by this trip
    trip_nodes = set()
    for arcs in paths.values():
        for u, v in arcs:
            trip_nodes.add(u)
            trip_nodes.add(v)
    
    trip_nodes_in_graph = [n for n in trip_nodes if n in G.nodes()]
    nx.draw_networkx_nodes(G, pos, nodelist=trip_nodes_in_graph, ax=ax,
                          node_color='yellow', node_size=600,
                          edgecolors='black', linewidths=2, alpha=0.9)
    
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=9, font_weight='bold')
    
    # Get trip info
    trip_info = trips_df[trips_df['trip_id'] == trip_id].iloc[0]
    origin = trip_info['origin']
    destination = trip_info['destination']
    demand = trip_info['demand']
    
    ax.set_title(f'Trip {trip_id}: {origin} → {destination} (Domanda: {demand} veicoli)', 
                fontsize=16, fontweight='bold')
    ax.legend(loc='upper right', fontsize=12, framealpha=0.9)
    ax.axis('off')
    
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/individual_paths/trip_{trip_id}_paths.png",
               dpi=200, bbox_inches='tight')
    plt.close()

print(f"✓ Salvati {len(example_trips)} grafici di percorsi individuali")

# ============================================================================
# STATISTICHE ARCHI IN COMUNE - EXCEL
# ============================================================================
print("\n📊 Creazione Excel con statistiche archi condivisi...")

# Create dataframe with arc usage statistics
arc_stats_rows = []

for arc, stats in sorted(arc_usage_stats.items(), 
                        key=lambda x: x[1]['n_trips'], 
                        reverse=True):
    arc_stats_rows.append({
        'Arc_From': arc[0],
        'Arc_To': arc[1],
        'Arc_ID': f"{arc[0]}_{arc[1]}",
        'N_Trips_Using': stats['n_trips'],
        'N_Paths_Using': stats['n_paths'],
        'Trip_IDs': ','.join(map(str, stats['trip_ids'][:20])) + ('...' if len(stats['trip_ids']) > 20 else '')
    })

arc_stats_df = pd.DataFrame(arc_stats_rows)

# Create Excel with multiple sheets
with pd.ExcelWriter(f"{OUTPUT_DIR}/arc_sharing_statistics.xlsx") as writer:
    # Sheet 1: All arcs
    arc_stats_df.to_excel(writer, sheet_name='All_Arcs', index=False)
    
    # Sheet 2: Shared arcs only (used by 2+ trips)
    shared_only = arc_stats_df[arc_stats_df['N_Trips_Using'] > 1]
    shared_only.to_excel(writer, sheet_name='Shared_Arcs', index=False)
    
    # Sheet 3: Top 50 most shared
    top_50 = arc_stats_df.head(50)
    top_50.to_excel(writer, sheet_name='Top_50_Shared', index=False)
    
    # Sheet 4: Arc usage matrix (trip x arc)
    # Too large for all, create for top 30 arcs and all trips
    top_30_arcs = [(row['Arc_From'], row['Arc_To']) for _, row in arc_stats_df.head(30).iterrows()]
    
    usage_matrix = []
    for trip_id in sorted(paths_dict.keys()):
        row = {'Trip_ID': trip_id}
        for arc in top_30_arcs:
            # Check if this trip uses this arc
            uses_arc = False
            for path_id, arcs in paths_dict[trip_id].items():
                if arc in arcs:
                    uses_arc = True
                    break
            row[f"{arc[0]}→{arc[1]}"] = 1 if uses_arc else 0
        usage_matrix.append(row)
    
    usage_df = pd.DataFrame(usage_matrix)
    usage_df.to_excel(writer, sheet_name='Usage_Matrix_Top30', index=False)

print(f"✓ Salvato: arc_sharing_statistics.xlsx")

# ============================================================================
# GRAFICO DISTRIBUZIONE SHARING
# ============================================================================
print("\n📈 Creazione grafico distribuzione sharing...")

fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Plot 1: Histogram of trips per arc
ax = axes[0, 0]
trips_per_arc = [stats['n_trips'] for stats in arc_usage_stats.values()]
ax.hist(trips_per_arc, bins=range(1, max(trips_per_arc)+2), 
       color='#2E86AB', alpha=0.7, edgecolor='black', linewidth=1.5)
ax.set_xlabel('Numero di Trip che Usano l\'Arco', fontweight='bold', fontsize=12)
ax.set_ylabel('Numero di Archi', fontweight='bold', fontsize=12)
ax.set_title('Distribuzione: Quanti Trip Usano Ogni Arco', fontweight='bold', fontsize=13)
ax.grid(axis='y', alpha=0.3)
ax.axvline(np.mean(trips_per_arc), color='red', linestyle='--', 
          linewidth=2, label=f'Media: {np.mean(trips_per_arc):.1f}')
ax.legend(fontsize=11)

# Plot 2: Bar chart top 20 archi
ax = axes[0, 1]
top_20_data = arc_stats_df.head(20)
y_pos = np.arange(len(top_20_data))
ax.barh(y_pos, top_20_data['N_Trips_Using'], 
       color='#A23B72', alpha=0.8, edgecolor='black', linewidth=1.5)
ax.set_yticks(y_pos)
ax.set_yticklabels([f"{row['Arc_From']}→{row['Arc_To']}" 
                    for _, row in top_20_data.iterrows()], fontsize=9)
ax.set_xlabel('Numero di Trip', fontweight='bold', fontsize=12)
ax.set_title('Top 20 Archi Più Condivisi', fontweight='bold', fontsize=13)
ax.invert_yaxis()
ax.grid(axis='x', alpha=0.3)

# Plot 3: Arcs by sharing level
ax = axes[1, 0]
sharing_levels = {
    'Esclusivi\n(1 trip)': len([s for s in arc_usage_stats.values() if s['n_trips'] == 1]),
    'Condivisi\n(2-5 trip)': len([s for s in arc_usage_stats.values() if 2 <= s['n_trips'] <= 5]),
    'Molto condivisi\n(6-10 trip)': len([s for s in arc_usage_stats.values() if 6 <= s['n_trips'] <= 10]),
    'Estremamente\ncondivisi (>10)': len([s for s in arc_usage_stats.values() if s['n_trips'] > 10])
}

colors_sharing = ['#2ECC71', '#F39C12', '#E67E22', '#E74C3C']
bars = ax.bar(range(len(sharing_levels)), sharing_levels.values(),
             color=colors_sharing, alpha=0.8, edgecolor='black', linewidth=2)
ax.set_xticks(range(len(sharing_levels)))
ax.set_xticklabels(sharing_levels.keys(), fontsize=10)
ax.set_ylabel('Numero di Archi', fontweight='bold', fontsize=12)
ax.set_title('Classificazione Archi per Livello di Condivisione', fontweight='bold', fontsize=13)
ax.grid(axis='y', alpha=0.3)

# Annotate bars
for i, (bar, (label, value)) in enumerate(zip(bars, sharing_levels.items())):
    ax.text(bar.get_x() + bar.get_width()/2, value + 5, str(value),
           ha='center', fontweight='bold', fontsize=11)

# Plot 4: Paths per arc
ax = axes[1, 1]
paths_per_arc = [stats['n_paths'] for stats in arc_usage_stats.values()]
ax.hist(paths_per_arc, bins=30, color='#F18F01', alpha=0.7, 
       edgecolor='black', linewidth=1.5)
ax.set_xlabel('Numero di Path che Usano l\'Arco', fontweight='bold', fontsize=12)
ax.set_ylabel('Numero di Archi', fontweight='bold', fontsize=12)
ax.set_title('Distribuzione: Quanti Path Usano Ogni Arco', fontweight='bold', fontsize=13)
ax.grid(axis='y', alpha=0.3)
ax.axvline(np.mean(paths_per_arc), color='red', linestyle='--',
          linewidth=2, label=f'Media: {np.mean(paths_per_arc):.1f}')
ax.legend(fontsize=11)

plt.tight_layout()
plt.savefig(f"{OUTPUT_DIR}/arc_sharing_distribution.png", dpi=300, bbox_inches='tight')
plt.close()
print(f"✓ Salvato: arc_sharing_distribution.png")

# ============================================================================
# REPORT FINALE
# ============================================================================
print("\n📝 Creazione report finale...")

# Extract sharing levels values for report
exclusive_arcs = sharing_levels['Esclusivi\n(1 trip)']
shared_2_5 = sharing_levels['Condivisi\n(2-5 trip)']
shared_6_10 = sharing_levels['Molto condivisi\n(6-10 trip)']
extreme_shared = sharing_levels['Estremamente\ncondivisi (>10)']

report = f"""
================================================================================
REPORT ANALISI RETE E PERCORSI - ARCHI IN COMUNE
================================================================================

DATI GENERALI:
- Trip totali: {len(paths_dict)}
- Percorsi totali: {total_paths}
- Nodi nella rete: {G.number_of_nodes()}
- Archi nella rete: {G.number_of_edges()}

STATISTICHE UTILIZZO ARCHI:
- Archi effettivamente usati: {len(arc_usage_stats)}
- Archi usati da 1 solo trip: {exclusive_arcs}
- Archi condivisi (2+ trip): {len(shared_arcs)}
- Media trip per arco: {np.mean(trips_per_arc):.2f}
- Max trip su un arco: {max(trips_per_arc)}

TOP 10 ARCHI PIÙ CONDIVISI:
"""

for i, (arc, stats) in enumerate(top_shared[:10], 1):
    report += f"\n{i}. {arc[0]} → {arc[1]}"
    report += f"\n   - Usato da {stats['n_trips']} trip diversi"
    report += f"\n   - Usato da {stats['n_paths']} path totali"
    report += f"\n   - Trip IDs: {', '.join(map(str, sorted(stats['trip_ids'])[:10]))}"
    if len(stats['trip_ids']) > 10:
        report += f" ... (+{len(stats['trip_ids'])-10} altri)"
    report += "\n"

report += f"""
CLASSIFICAZIONE ARCHI:
- Esclusivi (1 trip): {exclusive_arcs} archi ({exclusive_arcs/len(arc_usage_stats)*100:.1f}%)
- Condivisi (2-5 trip): {shared_2_5} archi ({shared_2_5/len(arc_usage_stats)*100:.1f}%)
- Molto condivisi (6-10 trip): {shared_6_10} archi ({shared_6_10/len(arc_usage_stats)*100:.1f}%)
- Estremamente condivisi (>10 trip): {extreme_shared} archi ({extreme_shared/len(arc_usage_stats)*100:.1f}%)

FILE GENERATI:
- network_with_shared_arcs.png: Rete con archi colorati per sharing
- arc_sharing_distribution.png: Distribuzione statistiche sharing
- arc_sharing_statistics.xlsx: Excel con tutte le statistiche
- individual_paths/trip_*_paths.png: Visualizzazione percorsi per trip (primi 10)

================================================================================
"""

with open(f"{OUTPUT_DIR}/REPORT_ARC_SHARING.txt", "w", encoding='utf-8') as f:
    f.write(report)

print(report)

print("\n" + "="*80)
print("✅ ANALISI COMPLETA TERMINATA CON SUCCESSO!")
print("="*80)
print(f"\nTutti i file salvati in: {OUTPUT_DIR}")
print("\n🎯 PROSSIMI STEP:")
print("  - Rivedi le visualizzazioni generate")
print("  - Analizza gli archi più condivisi nell'Excel")
print("  - Usa questi risultati per identificare colli di bottiglia")
print("  - Integra con l'app interattiva per esplorare trip specifici")
print("="*80)