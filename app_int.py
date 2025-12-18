import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.gridspec import GridSpec
import json
import networkx as nx
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURAZIONE PAGINA
# ============================================================================
st.set_page_config(
    page_title="Analisi Traffico 250 Trip",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.big-font {
    font-size:30px !important;
    font-weight: bold;
}
.metric-card {
    background-color: #f0f2f6;
    padding: 20px;
    border-radius: 10px;
    border-left: 5px solid #2E86AB;
}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# CARICA DATI
# ============================================================================
@st.cache_data
def load_data(excel_file):
    """Carica tutti i dati dall'Excel"""
    summary_df = pd.read_excel(excel_file, sheet_name='Summary')
    convergence_df = pd.read_excel(excel_file, sheet_name='Convergence')
    arc_stats_df = pd.read_excel(excel_file, sheet_name='Arc_Statistics')
    assignments_df = pd.read_excel(excel_file, sheet_name='Assignments')
    
    return summary_df, convergence_df, arc_stats_df, assignments_df

@st.cache_data
def load_network_data():
    """Carica dati della rete (nodi, archi, percorsi)"""
    try:
        with open('dati/nodes.json', 'r') as f:
            nodes_data = json.load(f)
        with open('dati/arcs_bidirectional.json', 'r') as f:
            arcs_data = json.load(f)
        with open('dati/trips_with_paths_temporal_15minuti_250.json', 'r') as f:
            trips_data = json.load(f)
        return nodes_data, arcs_data, trips_data
    except Exception as e:
        st.warning(f"⚠️ Impossibile caricare dati della rete: {e}")
        return None, None, None

EXCEL_FILE = "solution_ITERATIVE_UE_dataset_medium_traffic_250.xlsx"

try:
    summary_df, convergence_df, arc_stats_df, assignments_df = load_data(EXCEL_FILE)
    data_loaded = True
except:
    st.error(f"⚠️ Impossibile caricare {EXCEL_FILE}. Assicurati che il file sia nella directory corrente.")
    data_loaded = False
    st.stop()

# Carica dati della rete
nodes_data, arcs_data, trips_data = load_network_data()

# ============================================================================
# CALCOLA STATISTICHE
# ============================================================================
@st.cache_data
def compute_statistics(assignments_df):
    """Calcola statistiche aggregate"""
    trip_stats = assignments_df.groupby('Trip_ID').agg({
        'Demand': 'first',
        'FreeFlow_Time_min': 'first',
        'TravelTime_PWL_min': 'mean',
        'Inconvenience_PWL': 'mean',
        'Vehicles_Assigned': 'sum',
        'Path_ID': 'nunique',
        'Departure_Slot': ['min', 'max', 'nunique']
    }).reset_index()
    
    trip_stats.columns = ['Trip_ID', 'Demand', 'FreeFlow_Time', 'Avg_Travel_Time',
                         'Avg_Inconvenience', 'Total_Assigned', 'Num_Paths',
                         'Min_Slot', 'Max_Slot', 'Num_Slots']
    
    trip_stats['Congestion_Factor'] = trip_stats['Avg_Travel_Time'] / trip_stats['FreeFlow_Time']
    trip_stats['Assignment_Rate'] = (trip_stats['Total_Assigned'] / trip_stats['Demand']) * 100
    
    return trip_stats

trip_stats = compute_statistics(assignments_df)

# ============================================================================
# FUNZIONI PER VISUALIZZAZIONE PERCORSI
# ============================================================================
def plot_trip_paths(trip_id, nodes_data, arcs_data, trips_data):
    """Visualizza i percorsi di un trip sulla mappa del network"""
    
    if not all([nodes_data, arcs_data, trips_data]):
        st.warning("⚠️ Dati della rete non disponibili")
        return
    
    # Trova il trip nei dati
    trip_info = None
    for trip in trips_data['trips']:
        if trip['ID'] == f"trip_{int(trip_id)}":
            trip_info = trip
            break
    
    if not trip_info:
        st.warning(f"⚠️ Trip {int(trip_id)} non trovato nei dati")
        return
    
    # Crea dizionario nodi
    nodes_dict = {node['ID']: node for node in nodes_data['nodes']}
    
    # Crea grafo
    G = nx.DiGraph()
    
    # Aggiungi nodi
    for node in nodes_data['nodes']:
        G.add_node(node['ID'], pos=(node['lon'], node['lat']))
    
    # Aggiungi archi
    for arc in arcs_data['edges']:
        G.add_edge(arc['from_node'], arc['to_node'])
    
    # Prepara colori per i percorsi
    COLORS_PATHS = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A4C93', '#1982C4']
    
    # Crea figura
    fig, ax = plt.subplots(figsize=(16, 12))
    
    # Ottieni posizioni
    pos = nx.get_node_attributes(G, 'pos')
    
    # Disegna tutti i nodi (grigi e piccoli)
    nx.draw_networkx_nodes(G, pos, node_size=30, node_color='lightgray', 
                          alpha=0.5, ax=ax)
    
    # Disegna tutti gli archi (grigi e sottili)
    nx.draw_networkx_edges(G, pos, edge_color='lightgray', 
                          width=0.5, alpha=0.3, ax=ax, arrows=False)
    
    # Disegna ogni percorso del trip con colore diverso
    for idx, path in enumerate(trip_info['paths']):
        color = COLORS_PATHS[idx % len(COLORS_PATHS)]
        path_id = path['ID']
        
        # Estrai archi del percorso
        path_edges = [(arc[0], arc[1]) for arc in path['arcs']]
        
        # Disegna archi del percorso
        nx.draw_networkx_edges(G, pos, edgelist=path_edges,
                              edge_color=color, width=3, alpha=0.8,
                              ax=ax, arrows=True, arrowsize=15,
                              arrowstyle='->', label=f"Path {idx}")
        
        # Evidenzia nodi del percorso
        path_nodes = [arc[0] for arc in path['arcs']] + [path['arcs'][-1][1]]
        nx.draw_networkx_nodes(G, pos, nodelist=path_nodes,
                              node_size=80, node_color=color,
                              alpha=0.8, ax=ax)
    
    # Evidenzia origine e destinazione
    origin = trip_info['origin']
    destination = trip_info['destination']
    
    nx.draw_networkx_nodes(G, pos, nodelist=[origin],
                          node_size=300, node_color='green',
                          node_shape='s', label='Origine', ax=ax)
    nx.draw_networkx_nodes(G, pos, nodelist=[destination],
                          node_size=300, node_color='red',
                          node_shape='*', label='Destinazione', ax=ax)
    
    # Aggiungi label per origine e destinazione
    origin_name = nodes_dict.get(origin, {}).get('name', origin)
    dest_name = nodes_dict.get(destination, {}).get('name', destination)
    
    labels_od = {origin: origin_name, destination: dest_name}
    nx.draw_networkx_labels(G, pos, labels_od, font_size=9, 
                           font_weight='bold', ax=ax)
    
    ax.set_title(f'Percorsi del Trip {int(trip_id)}: {origin_name} → {dest_name}',
                fontsize=16, fontweight='bold')
    ax.axis('off')
    
    # Crea legend personalizzata
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='s', color='w', markerfacecolor='green', 
               markersize=12, label='Origine'),
        Line2D([0], [0], marker='*', color='w', markerfacecolor='red', 
               markersize=15, label='Destinazione')
    ]
    
    for idx, path in enumerate(trip_info['paths']):
        color = COLORS_PATHS[idx % len(COLORS_PATHS)]
        legend_elements.append(
            Line2D([0], [0], color=color, linewidth=3, label=f'Path {idx}')
        )
    
    ax.legend(handles=legend_elements, loc='upper right', fontsize=11)
    
    return fig

def plot_multiple_trips_with_shared_arcs(trip_ids, nodes_data, arcs_data, trips_data):
    """Visualizza più trip contemporaneamente evidenziando gli archi in comune"""
    
    if not all([nodes_data, arcs_data, trips_data]):
        st.warning("⚠️ Dati della rete non disponibili")
        return
    
    # Trova i trip nei dati
    trips_info = []
    for trip_id in trip_ids:
        for trip in trips_data['trips']:
            if trip['ID'] == f"trip_{int(trip_id)}":
                trips_info.append((trip_id, trip))
                break
    
    if not trips_info:
        st.warning("⚠️ Nessun trip trovato nei dati")
        return
    
    # Crea dizionario nodi
    nodes_dict = {node['ID']: node for node in nodes_data['nodes']}
    
    # Crea grafo
    G = nx.DiGraph()
    
    # Aggiungi nodi
    for node in nodes_data['nodes']:
        G.add_node(node['ID'], pos=(node['lon'], node['lat']))
    
    # Aggiungi archi
    for arc in arcs_data['edges']:
        G.add_edge(arc['from_node'], arc['to_node'])
    
    # Colori per i trip
    COLORS_TRIPS = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A4C93']
    
    # Raccogli tutti gli archi per ogni trip
    trip_arcs = {}
    all_arcs_list = []
    
    for idx, (trip_id, trip_info) in enumerate(trips_info):
        trip_edges = set()
        for path in trip_info['paths']:
            for arc in path['arcs']:
                edge = (arc[0], arc[1])
                trip_edges.add(edge)
                all_arcs_list.append(edge)
        trip_arcs[trip_id] = trip_edges
    
    # Trova archi condivisi (presenti in più di un trip)
    from collections import Counter
    arc_counter = Counter(all_arcs_list)
    shared_arcs = {arc for arc, count in arc_counter.items() if count > 1}
    
    # Crea figura
    fig, ax = plt.subplots(figsize=(18, 14))
    
    # Ottieni posizioni
    pos = nx.get_node_attributes(G, 'pos')
    
    # Disegna tutti i nodi (grigi e piccoli)
    nx.draw_networkx_nodes(G, pos, node_size=30, node_color='lightgray', 
                          alpha=0.5, ax=ax)
    
    # Disegna tutti gli archi (grigi e sottili)
    nx.draw_networkx_edges(G, pos, edge_color='lightgray', 
                          width=0.5, alpha=0.3, ax=ax, arrows=False)
    
    # Disegna prima gli archi CONDIVISI con evidenziazione speciale
    if shared_arcs:
        nx.draw_networkx_edges(G, pos, edgelist=list(shared_arcs),
                              edge_color='#FFD700', width=6, alpha=0.9,
                              ax=ax, arrows=True, arrowsize=20,
                              arrowstyle='->', style='solid')
    
    # Disegna gli archi di ogni trip
    all_origins = []
    all_destinations = []
    
    for idx, (trip_id, trip_info) in enumerate(trips_info):
        color = COLORS_TRIPS[idx % len(COLORS_TRIPS)]
        
        # Archi non condivisi di questo trip
        unique_arcs = trip_arcs[trip_id] - shared_arcs
        
        if unique_arcs:
            nx.draw_networkx_edges(G, pos, edgelist=list(unique_arcs),
                                  edge_color=color, width=2.5, alpha=0.7,
                                  ax=ax, arrows=True, arrowsize=12,
                                  arrowstyle='->')
        
        # Raccogli origini e destinazioni
        all_origins.append(trip_info['origin'])
        all_destinations.append(trip_info['destination'])
        
        # Evidenzia nodi del trip
        trip_nodes = set()
        for path in trip_info['paths']:
            for arc in path['arcs']:
                trip_nodes.add(arc[0])
                trip_nodes.add(arc[1])
        
        nx.draw_networkx_nodes(G, pos, nodelist=list(trip_nodes),
                              node_size=60, node_color=color,
                              alpha=0.6, ax=ax)
    
    # Evidenzia tutte le origini
    nx.draw_networkx_nodes(G, pos, nodelist=all_origins,
                          node_size=400, node_color='green',
                          node_shape='s', alpha=0.9, ax=ax,
                          edgecolors='black', linewidths=2)
    
    # Evidenzia tutte le destinazioni
    nx.draw_networkx_nodes(G, pos, nodelist=all_destinations,
                          node_size=400, node_color='red',
                          node_shape='*', alpha=0.9, ax=ax,
                          edgecolors='black', linewidths=2)
    
    # Aggiungi label per origini e destinazioni
    labels_od = {}
    for trip_id, trip_info in trips_info:
        origin = trip_info['origin']
        destination = trip_info['destination']
        origin_name = nodes_dict.get(origin, {}).get('name', origin)
        dest_name = nodes_dict.get(destination, {}).get('name', destination)
        labels_od[origin] = origin_name
        labels_od[destination] = dest_name
    
    nx.draw_networkx_labels(G, pos, labels_od, font_size=9, 
                           font_weight='bold', ax=ax)
    
    # Titolo con statistiche
    num_shared = len(shared_arcs)
    title = f'Confronto {len(trips_info)} Trip - {num_shared} Archi Condivisi'
    ax.set_title(title, fontsize=18, fontweight='bold')
    ax.axis('off')
    
    # Crea legend personalizzata
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='s', color='w', markerfacecolor='green', 
               markersize=14, label='Origini', markeredgecolor='black', markeredgewidth=2),
        Line2D([0], [0], marker='*', color='w', markerfacecolor='red', 
               markersize=16, label='Destinazioni', markeredgecolor='black', markeredgewidth=2),
        Line2D([0], [0], color='#FFD700', linewidth=6, label=f'Archi Condivisi ({num_shared})')
    ]
    
    for idx, (trip_id, trip_info) in enumerate(trips_info):
        color = COLORS_TRIPS[idx % len(COLORS_TRIPS)]
        origin_name = nodes_dict.get(trip_info['origin'], {}).get('name', trip_info['origin'])
        dest_name = nodes_dict.get(trip_info['destination'], {}).get('name', trip_info['destination'])
        legend_elements.append(
            Line2D([0], [0], color=color, linewidth=3, 
                   label=f'Trip {int(trip_id)}: {origin_name}→{dest_name}')
        )
    
    ax.legend(handles=legend_elements, loc='upper right', fontsize=11, 
             framealpha=0.95, edgecolor='black')
    
    # Aggiungi statistiche testuali
    stats_text = f"Totale archi usati: {len(set().union(*trip_arcs.values()))}\n"
    stats_text += f"Archi condivisi: {num_shared}\n"
    stats_text += f"Overlap: {num_shared/len(set().union(*trip_arcs.values()))*100:.1f}%"
    
    ax.text(0.02, 0.02, stats_text, transform=ax.transAxes,
           fontsize=11, verticalalignment='bottom',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    return fig

# ============================================================================
# SIDEBAR
# ============================================================================
st.sidebar.image("https://img.icons8.com/color/96/000000/traffic-jam.png", width=100)
st.sidebar.title("🚗 Analisi Traffico")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Seleziona Vista:",
    ["🏠 Dashboard Generale", "📊 Analisi Singolo Trip", "🔍 Confronta Trip", 
     "🗺️ Network Analysis", "📈 Statistiche Avanzate"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📋 Info Dataset")
st.sidebar.metric("Trip Totali", len(trip_stats))
st.sidebar.metric("Domanda Totale", f"{trip_stats['Demand'].sum():.0f}")
st.sidebar.metric("Iterazioni", len(convergence_df))
st.sidebar.metric("TSTT Finale", f"{convergence_df.iloc[-1]['TSTT']/1e6:.1f}M min")

# ============================================================================
# PAGINA 1: DASHBOARD GENERALE
# ============================================================================
if page == "🏠 Dashboard Generale":
    st.markdown('<p class="big-font">Dashboard Generale - 250 Trip</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Metriche principali
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Trip Totali", len(trip_stats))
    with col2:
        st.metric("Domanda Totale", f"{trip_stats['Demand'].sum():.0f} veicoli")
    with col3:
        st.metric("Congestione Media", f"{trip_stats['Congestion_Factor'].mean():.2f}x")
    
    
    st.markdown("---")
    
   
    
    # Distribuzione domanda e congestione
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Distribuzione Domanda")
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.hist(trip_stats['Demand'], bins=30, color='#2E86AB', alpha=0.7, edgecolor='black')
        ax.axvline(trip_stats['Demand'].mean(), color='red', linestyle='--',
                  linewidth=2, label=f"Media: {trip_stats['Demand'].mean():.0f}")
        ax.axvline(trip_stats['Demand'].median(), color='green', linestyle='--',
                  linewidth=2, label=f"Mediana: {trip_stats['Demand'].median():.0f}")
        ax.set_xlabel('Domanda (veicoli)', fontweight='bold')
        ax.set_ylabel('Numero di Trip', fontweight='bold')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        st.pyplot(fig)
        plt.close()
    
    with col2:
        st.subheader("🚦 Livelli di Congestione")
        congestion_bins = [0, 1.1, 1.3, 1.5, 2.0, 10]
        congestion_labels = ['Bassa\n(<10%)', 'Moderata\n(10-30%)', 
                           'Alta\n(30-50%)', 'Severa\n(50-100%)', 'Estrema\n(>100%)']
        trip_stats['Congestion_Level'] = pd.cut(trip_stats['Congestion_Factor'],
                                                bins=congestion_bins,
                                                labels=congestion_labels)
        
        counts = trip_stats['Congestion_Level'].value_counts().sort_index()
        colors = ['#2ECC71', '#F39C12', '#E67E22', '#E74C3C', '#8E44AD']
        
        fig, ax = plt.subplots(figsize=(8, 5))
        bars = ax.bar(range(len(counts)), counts.values,
                     color=colors[:len(counts)], alpha=0.8, edgecolor='black', linewidth=2)
        ax.set_xticks(range(len(counts)))
        ax.set_xticklabels(counts.index, fontsize=9)
        ax.set_ylabel('Numero di Trip', fontweight='bold')
        ax.grid(axis='y', alpha=0.3)
        
        # Annotate bars
        for i, (bar, v) in enumerate(zip(bars, counts.values)):
            ax.text(bar.get_x() + bar.get_width()/2, v + 1, str(v),
                   ha='center', fontweight='bold')
        
        st.pyplot(fig)
        plt.close()
    
    st.markdown("---")
    
    # Top trip congestionati
    st.subheader("🔴 Top 20 Trip Più Congestionati")
    top_congested = trip_stats.nlargest(20, 'Congestion_Factor')[
        ['Trip_ID', 'Demand', 'Congestion_Factor', 'Avg_Travel_Time', 'FreeFlow_Time', 'Num_Paths']
    ].copy()
    top_congested['Trip_ID'] = top_congested['Trip_ID'].astype(int)
    top_congested['Congestion_Factor'] = top_congested['Congestion_Factor'].round(2)
    top_congested['Avg_Travel_Time'] = top_congested['Avg_Travel_Time'].round(1)
    top_congested['FreeFlow_Time'] = top_congested['FreeFlow_Time'].round(1)
    
    st.dataframe(top_congested, use_container_width=True, height=400)

# ============================================================================
# PAGINA 2: ANALISI SINGOLO TRIP
# ============================================================================
elif page == "📊 Analisi Singolo Trip":
    st.markdown('<p class="big-font">Analisi Dettagliata Singolo Trip</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Seleziona trip
    selected_trip = st.selectbox(
        "Seleziona Trip da Analizzare:",
        sorted(trip_stats['Trip_ID'].unique()),
        format_func=lambda x: f"Trip {int(x)} (Domanda: {trip_stats[trip_stats['Trip_ID']==x]['Demand'].values[0]:.0f})"
    )
    
    # Filtra dati per il trip selezionato
    trip_data = assignments_df[assignments_df['Trip_ID'] == selected_trip].copy()
    trip_info = trip_stats[trip_stats['Trip_ID'] == selected_trip].iloc[0]
    
    # Metriche del trip
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Domanda", f"{trip_info['Demand']:.0f}")
    with col2:
        st.metric("Assegnati", f"{trip_info['Total_Assigned']:.1f}")
    with col3:
        st.metric("Percorsi", int(trip_info['Num_Paths']))
    with col4:
        st.metric("Congestione", f"{trip_info['Congestion_Factor']:.2f}x")
    with col5:
        late_departures = trip_data[trip_data['Departure_Slot'] > 108]['Vehicles_Assigned'].sum()
        on_time = late_departures == 0
        st.metric("Entro Slot 108", "✓ Sì" if on_time else f"✗ No")
    
    st.markdown("---")
    
    # VISUALIZZAZIONE PERCORSI SU MAPPA
    st.subheader("🗺️ Visualizzazione Percorsi su Rete Stradale")
    
    if all([nodes_data, arcs_data, trips_data]):
        fig = plot_trip_paths(selected_trip, nodes_data, arcs_data, trips_data)
        if fig:
            st.pyplot(fig)
            plt.close()
    else:
        st.info("💡 Assicurati che i file dati/nodes.json, dati/arcs_bidirectional.json e dati/trips_with_paths_temporal_15minuti_250.json siano presenti")
    
    st.markdown("---")
    
    # Grafici
    paths = sorted(trip_data['Path_ID'].unique())
    COLORS_PATHS = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A4C93', '#1982C4']
    
    # Row 1: Vehicle Distribution
    st.subheader("🚗 Distribuzione Veicoli nel Tempo")
    
    fig, ax = plt.subplots(figsize=(16, 5))
    pivot_data = trip_data.pivot_table(
        index='Departure_Slot',
        columns='Path_ID',
        values='Vehicles_Assigned',
        fill_value=0
    )
    
    ax.stackplot(pivot_data.index,
                [pivot_data[path] for path in paths],
                labels=[f'Path {int(path)}' for path in paths],
                colors=COLORS_PATHS[:len(paths)],
                alpha=0.8)
    ax.set_xlabel('Slot di Partenza', fontweight='bold', fontsize=12)
    ax.set_ylabel('Veicoli Assegnati', fontweight='bold', fontsize=12)
    ax.axvline(x=108, color='red', linestyle='--', linewidth=2, alpha=0.7, label='Limite Slot 108')
    ax.legend(loc='upper left', fontsize=11)
    ax.grid(True, alpha=0.3)
    st.pyplot(fig)
    plt.close()
    
    # Row 2: Path Split & Travel Times
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Path Split Percentage")
        fig, ax = plt.subplots(figsize=(8, 5))
        
        total_per_slot = trip_data.groupby('Departure_Slot')['Vehicles_Assigned'].sum()
        
        for i, path_id in enumerate(paths):
            path_data = trip_data[trip_data['Path_ID'] == path_id]
            percentages = (path_data.set_index('Departure_Slot')['Vehicles_Assigned'] / 
                          total_per_slot * 100)
            
            ax.plot(percentages.index, percentages.values,
                   marker='o', markersize=4, linewidth=2,
                   label=f'Path {int(path_id)}',
                   color=COLORS_PATHS[i % len(COLORS_PATHS)])
        
        ax.axhline(y=50, color='gray', linestyle='--', alpha=0.5, linewidth=2)
        ax.set_xlabel('Slot', fontweight='bold')
        ax.set_ylabel('% Veicoli', fontweight='bold')
        ax.set_ylim(0, 100)
        ax.legend()
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)
        plt.close()
    
    with col2:
        st.subheader("⏱️ Evoluzione Tempi di Viaggio")
        fig, ax = plt.subplots(figsize=(8, 5))
        
        for i, path_id in enumerate(paths):
            path_data = trip_data[trip_data['Path_ID'] == path_id].sort_values('Departure_Slot')
            
            ax.plot(path_data['Departure_Slot'],
                   path_data['TravelTime_PWL_min'],
                   marker='o', markersize=4, linewidth=2,
                   label=f'Path {int(path_id)}',
                   color=COLORS_PATHS[i % len(COLORS_PATHS)])
        
        free_flow = trip_data['FreeFlow_Time_min'].iloc[0]
        ax.axhline(y=free_flow, color='green', linestyle='--',
                  alpha=0.7, linewidth=2, label='Free Flow')
        
        ax.set_xlabel('Slot', fontweight='bold')
        ax.set_ylabel('Tempo (min)', fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)
        plt.close()
    
    # Row 3: Inconvenience & Statistics
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Inconvenience Evolution")
        fig, ax = plt.subplots(figsize=(8, 5))
        
        for i, path_id in enumerate(paths):
            path_data = trip_data[trip_data['Path_ID'] == path_id].sort_values('Departure_Slot')
            
            ax.plot(path_data['Departure_Slot'],
                   path_data['Inconvenience_PWL'],
                   marker='o', markersize=4, linewidth=2,
                   label=f'Path {int(path_id)}',
                   color=COLORS_PATHS[i % len(COLORS_PATHS)])
        
        ax.axhline(y=1.0, color='green', linestyle='--',
                  alpha=0.7, linewidth=2, label='No Inconvenience')
        ax.set_xlabel('Slot', fontweight='bold')
        ax.set_ylabel('Inconvenience', fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)
        plt.close()
    
    with col2:
        st.subheader("📋 Statistiche Dettagliate")
        
        stats_data = {
            'Metrica': [
                'Free-Flow Time (min)',
                'Tempo Medio Effettivo (min)',
                'Fattore Congestione',
                'Inconvenience Medio',
                'Slot Range',
                'Numero Slot Usati'
            ],
            'Valore': [
                f"{trip_info['FreeFlow_Time']:.1f}",
                f"{trip_info['Avg_Travel_Time']:.1f}",
                f"{trip_info['Congestion_Factor']:.2f}x",
                f"{trip_info['Avg_Inconvenience']:.3f}",
                f"{int(trip_info['Min_Slot'])}-{int(trip_info['Max_Slot'])}",
                f"{int(trip_info['Num_Slots'])}",
                f"{trip_info['Assignment_Rate']:.1f}"
            ]
        }
        
        st.dataframe(pd.DataFrame(stats_data), use_container_width=True, hide_index=True)

# ============================================================================
# PAGINA 3: CONFRONTA TRIP
# ============================================================================
elif page == "🔍 Confronta Trip":
    st.markdown('<p class="big-font">Confronto tra Trip Multipli</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Seleziona trip da confrontare
    selected_trips = st.multiselect(
        "Seleziona Trip da Confrontare (max 5):",
        sorted(trip_stats['Trip_ID'].unique()),
        default=sorted(trip_stats['Trip_ID'].unique())[:3],
        format_func=lambda x: f"Trip {int(x)}",
        max_selections=5
    )
    
    if len(selected_trips) < 2:
        st.warning("⚠️ Seleziona almeno 2 trip per il confronto")
    else:
        # Filtra dati
        compare_stats = trip_stats[trip_stats['Trip_ID'].isin(selected_trips)].copy()
        compare_stats['Trip_ID'] = compare_stats['Trip_ID'].astype(int)
        
        # Metriche comparative
        st.subheader("📊 Metriche Comparative")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            fig, ax = plt.subplots(figsize=(6, 5))
            ax.bar(range(len(compare_stats)), compare_stats['Demand'],
                  color='#2E86AB', alpha=0.8, edgecolor='black')
            ax.set_xticks(range(len(compare_stats)))
            ax.set_xticklabels([f"T{int(tid)}" for tid in compare_stats['Trip_ID']])
            ax.set_ylabel('Domanda (veicoli)', fontweight='bold')
            ax.set_title('Domanda', fontweight='bold')
            ax.grid(axis='y', alpha=0.3)
            st.pyplot(fig)
            plt.close()
        
        with col2:
            fig, ax = plt.subplots(figsize=(6, 5))
            ax.bar(range(len(compare_stats)), compare_stats['Congestion_Factor'],
                  color='#A23B72', alpha=0.8, edgecolor='black')
            ax.set_xticks(range(len(compare_stats)))
            ax.set_xticklabels([f"T{int(tid)}" for tid in compare_stats['Trip_ID']])
            ax.set_ylabel('Fattore', fontweight='bold')
            ax.set_title('Congestione', fontweight='bold')
            ax.axhline(y=1.0, color='green', linestyle='--', linewidth=2)
            ax.grid(axis='y', alpha=0.3)
            st.pyplot(fig)
            plt.close()
        
        with col3:
            fig, ax = plt.subplots(figsize=(6, 5))
            ax.bar(range(len(compare_stats)), compare_stats['Num_Paths'],
                  color='#F18F01', alpha=0.8, edgecolor='black')
            ax.set_xticks(range(len(compare_stats)))
            ax.set_xticklabels([f"T{int(tid)}" for tid in compare_stats['Trip_ID']])
            ax.set_ylabel('Numero', fontweight='bold')
            ax.set_title('Percorsi Alternativi', fontweight='bold')
            ax.grid(axis='y', alpha=0.3)
            st.pyplot(fig)
            plt.close()
        
        # Tabella comparativa
        st.subheader("📋 Tabella Comparativa Dettagliata")
        compare_display = compare_stats[[
            'Trip_ID', 'Demand', 'Congestion_Factor', 'Avg_Travel_Time',
            'FreeFlow_Time', 'Num_Paths', 'Assignment_Rate', 'Avg_Inconvenience'
        ]].copy()
        
        compare_display.columns = [
            'Trip', 'Domanda', 'Cong.Factor', 'Tempo Avg', 
            'Free-Flow', 'N.Paths', 'Assign%', 'Inconv.Avg'
        ]
        
        # Round numbers
        for col in compare_display.columns[1:]:
            if compare_display[col].dtype != 'int64':
                compare_display[col] = compare_display[col].round(2)
        
        st.dataframe(compare_display, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # VISUALIZZAZIONE NETWORK CON ARCHI CONDIVISI
        st.subheader("🗺️ Visualizzazione Network - Archi Condivisi")
        
        if all([nodes_data, arcs_data, trips_data]):
            fig = plot_multiple_trips_with_shared_arcs(selected_trips, nodes_data, 
                                                       arcs_data, trips_data)
            if fig:
                st.pyplot(fig)
                plt.close()
                
                # Aggiungi info box
                st.info("""
                **Legenda:**
                - 🟢 **Quadrati verdi**: Origini dei trip
                - 🔴 **Stelle rosse**: Destinazioni dei trip
                - 🟡 **Archi dorati spessi**: Archi condivisi tra più trip (punti critici della rete!)
                - **Archi colorati**: Archi specifici di ciascun trip
                
                Gli archi condivisi rappresentano i **bottleneck** della rete dove più flussi di traffico si sovrappongono.
                """)
        else:
            st.info("💡 Assicurati che i file dati/nodes.json, dati/arcs_bidirectional.json e dati/trips_with_paths_temporal_15minuti_250.json siano presenti")

# ============================================================================
# PAGINA 4: NETWORK ANALYSIS
# ============================================================================
elif page == "🗺️ Network Analysis":
    st.markdown('<p class="big-font">Analisi della Rete</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    st.info("🚧 Sezione in sviluppo: Visualizzazione grafo della rete con percorsi e archi in comune")
    
    st.subheader("📊 Statistiche Archi")
    
    # Top archi più utilizzati
    top_arcs = arc_stats_df.nlargest(20, 'Ave_Ave_Util')[
        ['From', 'To', 'Ave_Ave_Flow', 'Ave_Ave_Util', 'Max_Max_Flow', 'Max_Max_Util']
    ].copy()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Top 20 Archi per Utilizzo Medio**")
        st.dataframe(top_arcs, use_container_width=True, hide_index=True, height=400)
    
    with col2:
        st.write("**Distribuzione Utilizzo Archi**")
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.hist(arc_stats_df['Ave_Ave_Util'], bins=30, 
               color='#2E86AB', alpha=0.7, edgecolor='black')
        ax.set_xlabel('Utilizzo Medio (%)', fontweight='bold')
        ax.set_ylabel('Numero di Archi', fontweight='bold')
        ax.axvline(arc_stats_df['Ave_Ave_Util'].mean(), color='red',
                  linestyle='--', linewidth=2, label=f"Media: {arc_stats_df['Ave_Ave_Util'].mean():.1f}%")
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        st.pyplot(fig)
        plt.close()
    
    st.markdown("---")
    st.info("💡 I percorsi su grafo sono ora visualizzabili nella sezione 'Analisi Singolo Trip'")

# ============================================================================
# PAGINA 5: STATISTICHE AVANZATE
# ============================================================================
elif page == "📈 Statistiche Avanzate":
    st.markdown('<p class="big-font">Statistiche Avanzate e Pattern</p>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Correlazioni
    st.subheader("🔗 Analisi Correlazioni")
    
    correlation_data = trip_stats[['Demand', 'Congestion_Factor', 'Avg_Travel_Time',
                                   'Num_Paths', 'Assignment_Rate', 'Avg_Inconvenience']].corr()
    
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(correlation_data, annot=True, cmap='coolwarm', center=0,
               square=True, linewidths=1, cbar_kws={"shrink": 0.8}, ax=ax)
    ax.set_title('Matrice di Correlazione', fontweight='bold', fontsize=14)
    st.pyplot(fig)
    plt.close()
    
    st.markdown("---")
    
    # Scatter plots
    st.subheader("📊 Relazioni tra Variabili")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig, ax = plt.subplots(figsize=(8, 6))
        scatter = ax.scatter(trip_stats['Demand'], trip_stats['Congestion_Factor'],
                           c=trip_stats['Num_Paths'], cmap='viridis',
                           s=100, alpha=0.6, edgecolors='black')
        ax.set_xlabel('Domanda (veicoli)', fontweight='bold')
        ax.set_ylabel('Fattore di Congestione', fontweight='bold')
        ax.set_title('Domanda vs Congestione', fontweight='bold')
        ax.grid(True, alpha=0.3)
        plt.colorbar(scatter, ax=ax, label='N. Percorsi')
        st.pyplot(fig)
        plt.close()
    
    with col2:
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.scatter(trip_stats['Num_Paths'], trip_stats['Congestion_Factor'],
                  c='#A23B72', s=100, alpha=0.6, edgecolors='black')
        ax.set_xlabel('Numero di Percorsi', fontweight='bold')
        ax.set_ylabel('Fattore di Congestione', fontweight='bold')
        ax.set_title('Percorsi vs Congestione', fontweight='bold')
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)
        plt.close()
    
    st.markdown("---")
    
    # Temporal patterns
    st.subheader("⏰ Pattern Temporali Aggregati")
    
    slot_distribution = assignments_df.groupby('Departure_Slot')['Vehicles_Assigned'].sum()
    
    fig, ax = plt.subplots(figsize=(16, 5))
    ax.fill_between(slot_distribution.index, slot_distribution.values,
                    alpha=0.7, color='#2E86AB', edgecolor='black', linewidth=2)
    ax.set_xlabel('Slot di Partenza', fontweight='bold', fontsize=12)
    ax.set_ylabel('Veicoli Totali', fontweight='bold', fontsize=12)
    ax.set_title('Distribuzione Temporale Aggregata - Tutti i Trip', fontweight='bold', fontsize=14)
    ax.axvline(x=108, color='red', linestyle='--', linewidth=3, label='Limite Slot 108')
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=11)
    st.pyplot(fig)
    plt.close()

# ============================================================================
# FOOTER
# ============================================================================
st.sidebar.markdown("---")
st.sidebar.markdown("### 💡 Info")
st.sidebar.info(
    "App interattiva per l'analisi di 250 trip con User Equilibrium iterativo. "
    "Usa il menu sopra per esplorare diverse viste e analisi."
)

st.sidebar.markdown("---")
st.sidebar.success("✅ Dati caricati correttamente!")