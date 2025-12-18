"""
Network Traffic Visualization with TIME-SPECIFIC Data
Generates PNG images and LaTeX TikZ code showing actual traffic at 8AM, 12PM, and 6PM
WINDOWS COMPATIBLE - Uses time-specific flow data
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import pandas as pd
import glob
import os

# ==============================================================
# TIME SLOT CALCULATION  
# ==============================================================
SNAPSHOTS = {
    "8AM": 32,
    "12PM": 48,
    "6PM": 72
}

def find_solution_file():
    """Auto-detect solution Excel file"""
    patterns = ["solution_ITERATIVE_UE*.xlsx", "solution_250*.xlsx", "solution*.xlsx"]
    for pattern in patterns:
        files = glob.glob(pattern)
        if files:
            return files[0]
    return None

def load_network_data():
    """Load nodes and edges from JSON files"""
    with open('dati/nodes.json', 'r', encoding='utf-8') as f:
        nodes_data = json.load(f)
    with open('dati/arcs_bidirectional.json', 'r', encoding='utf-8') as f:
        edges_data = json.load(f)
    return nodes_data, edges_data

def load_time_specific_flows_from_json(json_file="arc_flows_by_time.json"):
    """
    Load time-specific flow data from JSON export
    Returns: dict mapping (time_slot) -> {(from, to): flow}
    """
    print(f"[INFO] Loading time-specific flows from {json_file}...")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        flows_by_time = json.load(f)
    
    # Reorganize: time -> arc -> flow
    flows_by_slot = {}
    
    for arc_key, time_flows in flows_by_time.items():
        from_node, to_node = arc_key.split(',')
        
        for time_str, flow in time_flows.items():
            t = int(time_str)
            if t not in flows_by_slot:
                flows_by_slot[t] = {}
            flows_by_slot[t][(from_node, to_node)] = float(flow)
    
    print(f"[OK] Loaded flows for {len(flows_by_slot)} time slots")
    return flows_by_slot

def load_time_specific_flows_from_excel(excel_file):
    """
    Load time-specific flow data from detailed Excel export
    """
    print(f"[INFO] Loading time-specific flows from {excel_file}...")
    
    # Check for detailed Excel file
    if os.path.exists("arc_flows_detailed.xlsx"):
        excel_file = "arc_flows_detailed.xlsx"
        print(f"[INFO] Found detailed flow file: {excel_file}")
    
    try:
        df = pd.read_excel(excel_file, sheet_name="Arc_Flows_By_Time")
        
        # Extract flows for each time
        flows_by_slot = {}
        
        # Slot 8 (8AM)
        flows_by_slot[8] = {}
        for _, row in df.iterrows():
            from_node = str(row['From'])
            to_node = str(row['To'])
            flows_by_slot[8][(from_node, to_node)] = float(row['Flow_8AM_Slot8'])
        
        # Slot 24 (12PM)
        flows_by_slot[24] = {}
        for _, row in df.iterrows():
            from_node = str(row['From'])
            to_node = str(row['To'])
            flows_by_slot[24][(from_node, to_node)] = float(row['Flow_12PM_Slot24'])
        
        # Slot 48 (6PM)
        flows_by_slot[48] = {}
        for _, row in df.iterrows():
            from_node = str(row['From'])
            to_node = str(row['To'])
            flows_by_slot[48][(from_node, to_node)] = float(row['Flow_6PM_Slot48'])
        
        print(f"[OK] Loaded time-specific flows for 3 time slots")
        return flows_by_slot
        
    except Exception as e:
        print(f"[ERROR] Could not load time-specific flows: {e}")
        return None

def normalize_flows(arc_flows, percentile=95):
    """Normalize flows for visualization"""
    flows = list(arc_flows.values())
    if not flows:
        return arc_flows, 0, 0
    
    min_flow = 0
    max_flow = np.percentile(flows, percentile)
    
    normalized = {}
    for arc, flow in arc_flows.items():
        norm_flow = min(flow / max_flow, 1.0) if max_flow > 0 else 0
        normalized[arc] = norm_flow
    
    return normalized, min_flow, max_flow

def create_traffic_visualization(nodes_data, edges_data, arc_flows, time_label, slot_number):
    """Create matplotlib visualization of network traffic"""
    nodes = nodes_data['nodes']
    node_positions = {node['ID']: (float(node['lon']), float(node['lat'])) for node in nodes}
    
    normalized_flows, min_flow, max_flow = normalize_flows(arc_flows)
    
    fig, ax = plt.subplots(figsize=(20, 16))
    
    # Draw edges with thickness based on flow
    edges = edges_data['edges']
    for edge in edges:
        from_id = str(edge['from_node'])
        to_id = str(edge['to_node'])
        
        if from_id not in node_positions or to_id not in node_positions:
            continue
        
        x1, y1 = node_positions[from_id]
        x2, y2 = node_positions[to_id]
        
        flow_key = (from_id, to_id)
        intensity = normalized_flows.get(flow_key, 0.0)
        
        linewidth = 0.5 + intensity * 4.5
        
        if intensity < 0.2:
            color = '#CCCCCC'
        elif intensity < 0.4:
            color = '#FF9999'
        elif intensity < 0.6:
            color = '#FF6666'
        elif intensity < 0.8:
            color = '#FF3333'
        else:
            color = '#CC0000'
        
        ax.plot([x1, x2], [y1, y2], color=color, linewidth=linewidth, alpha=0.7, zorder=1)
    
    # Draw nodes
    for node in nodes:
        node_id = node['ID']
        if node_id not in node_positions:
            continue
        
        x, y = node_positions[node_id]
        category = node.get('category', 'bassa_domanda')
        
        if 'estero' in category:
            node_color, node_size = '#4169E1', 150
        elif 'turistica' in category:
            node_color, node_size = '#32CD32', 120
        elif 'grande_domanda' in category:
            node_color, node_size = '#FF4500', 120
        else:
            node_color, node_size = '#808080', 80
        
        ax.scatter(x, y, c=node_color, s=node_size, zorder=2, edgecolors='black', linewidths=0.5)
        
        if node_size > 80:
            ax.annotate(node.get('name', node_id), (x, y), fontsize=7, ha='center', va='bottom', zorder=3)
    
    # Legend
    legend_elements = [
        Line2D([0], [0], color='#CCCCCC', linewidth=2, label='Low Traffic (0-20%)'),
        Line2D([0], [0], color='#FF9999', linewidth=2.5, label='Light (20-40%)'),
        Line2D([0], [0], color='#FF6666', linewidth=3.5, label='Medium (40-60%)'),
        Line2D([0], [0], color='#FF3333', linewidth=4.5, label='Heavy (60-80%)'),
        Line2D([0], [0], color='#CC0000', linewidth=5, label='Very Heavy (80-100%)'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#4169E1', markersize=10, label='Border'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#32CD32', markersize=10, label='Tourist'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#FF4500', markersize=10, label='High Demand'),
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=10)
    
    ax.set_title(f'Northern Italy Highway Network - {time_label} (Slot {slot_number})', fontsize=16, fontweight='bold')
    ax.set_xlabel('Longitude', fontsize=12)
    ax.set_ylabel('Latitude', fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')
    plt.tight_layout()
    
    return fig, normalized_flows, min_flow, max_flow

def generate_latex_tikz(nodes_data, edges_data, arc_flows, time_label, slot_number):
    """Generate LaTeX TikZ code"""
    nodes = nodes_data['nodes']
    edges = edges_data['edges']
    normalized_flows, min_flow, max_flow = normalize_flows(arc_flows)
    
    lons = [float(n['lon']) for n in nodes]
    lats = [float(n['lat']) for n in nodes]
    lon_min, lon_max = min(lons), max(lons)
    lat_min, lat_max = min(lats), max(lats)
    
    scale_x = 15.0 / (lon_max - lon_min)
    scale_y = 15.0 / (lat_max - lat_min)
    
    def scale_coords(lon, lat):
        return (lon - lon_min) * scale_x, (lat - lat_min) * scale_y
    
    latex = []
    latex.append("\\begin{tikzpicture}[scale=0.8]")
    latex.append(f"  % Traffic at {time_label} (Slot {slot_number})")
    latex.append("")
    latex.append("  % Highway arcs")
    
    for edge in edges:
        from_id, to_id = str(edge['from_node']), str(edge['to_node'])
        from_node = next((n for n in nodes if n['ID'] == from_id), None)
        to_node = next((n for n in nodes if n['ID'] == to_id), None)
        
        if not from_node or not to_node:
            continue
        
        x1, y1 = scale_coords(float(from_node['lon']), float(from_node['lat']))
        x2, y2 = scale_coords(float(to_node['lon']), float(to_node['lat']))
        
        intensity = normalized_flows.get((from_id, to_id), 0.0)
        linewidth = 0.3 + intensity * 2.7
        
        if intensity < 0.2:
            color = 'gray!30'
        elif intensity < 0.4:
            color = 'red!30'
        elif intensity < 0.6:
            color = 'red!50'
        elif intensity < 0.8:
            color = 'red!70'
        else:
            color = 'red!90'
        
        latex.append(f"  \\draw[{color}, line width={linewidth:.2f}pt, opacity=0.7] ({x1:.2f},{y1:.2f}) -- ({x2:.2f},{y2:.2f});")
    
    latex.append("")
    latex.append("  % Nodes")
    for node in nodes:
        x, y = scale_coords(float(node['lon']), float(node['lat']))
        category = node.get('category', 'bassa_domanda')
        
        if 'estero' in category:
            style = "fill=blue!60, circle, minimum size=4pt"
        elif 'turistica' in category:
            style = "fill=green!60, circle, minimum size=3pt"
        elif 'grande_domanda' in category:
            style = "fill=orange!60, circle, minimum size=3pt"
        else:
            style = "fill=gray!40, circle, minimum size=2pt"
        
        latex.append(f"  \\node[{style}] at ({x:.2f},{y:.2f}) {{}};")
    
    latex.append("")
    latex.append("  % Legend")
    latex.append("  \\node[anchor=north east, font=\\footnotesize] at (15, 15) {")
    latex.append(f"    \\begin{{tabular}}{{l}}")
    latex.append(f"      \\textbf{{{time_label}}} \\\\")
    latex.append(f"      Slot: {slot_number} \\\\")
    latex.append(f"      Max: {max_flow:.0f} veh \\\\")
    latex.append("    \\end{tabular}")
    latex.append("  };")
    latex.append("\\end{tikzpicture}")
    
    return "\n".join(latex)

def main():
    """Main execution"""
    print("="*60)
    print("TIME-SPECIFIC Traffic Visualization")
    print("="*60)
    
    nodes_data, edges_data = load_network_data()
    print(f"  Loaded {len(nodes_data['nodes'])} nodes and {len(edges_data['edges'])} edges")
    
    # Try to load time-specific flows
    flows_by_slot = None
    
    # Option 1: Try JSON file
    if os.path.exists("arc_flows_by_time.json"):
        flows_by_slot = load_time_specific_flows_from_json("arc_flows_by_time.json")
    
    # Option 2: Try detailed Excel file
    if flows_by_slot is None and os.path.exists("arc_flows_detailed.xlsx"):
        flows_by_slot = load_time_specific_flows_from_excel("arc_flows_detailed.xlsx")
    
    # Option 3: Try main solution file
    if flows_by_slot is None:
        solution_file = find_solution_file()
        if solution_file:
            flows_by_slot = load_time_specific_flows_from_excel(solution_file)
    
    if flows_by_slot is None:
        print("\n[ERROR] No time-specific flow data found!")
        print("[INFO] You need to export time-specific flows first.")
        print("[INFO] Add this to the END of your solve_1.py:")
        print("")
        print("from export_flows import export_time_specific_flows, export_to_excel_with_time")
        print("export_time_specific_flows(model, ARCS, TIME_SLOTS, 'arc_flows_by_time.json')")
        print("export_to_excel_with_time(model, ARCS, TIME_SLOTS, FFTT, CAPACITY, 'arc_flows_detailed.xlsx')")
        print("")
        print("[INFO] Then run your solve script again to create the time-specific data files.")
        return
    
    # Generate visualizations
    latex_outputs = []
    
    for time_label, slot in SNAPSHOTS.items():
        if slot not in flows_by_slot:
            print(f"[WARNING] No data for slot {slot} ({time_label})")
            continue
        
        print(f"\n{'='*60}")
        print(f"Generating {time_label} (Slot {slot})")
        print(f"{'='*60}")
        
        arc_flows = flows_by_slot[slot]
        
        fig, _, min_flow, max_flow = create_traffic_visualization(
            nodes_data, edges_data, arc_flows, time_label, slot
        )
        
        output_file = f"network_traffic_{time_label.replace(':', '')}.png"
        fig.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"  Saved PNG: {output_file}")
        plt.close(fig)
        
        tikz_code = generate_latex_tikz(nodes_data, edges_data, arc_flows, time_label, slot)
        latex_file = f"network_traffic_{time_label.replace(':', '')}.tex"
        with open(latex_file, 'w', encoding='utf-8') as f:
            f.write(tikz_code)
        print(f"  Saved LaTeX: {latex_file}")
        
        latex_outputs.append({'time': time_label, 'slot': slot, 'code': tikz_code})
        
        flows = list(arc_flows.values())
        print(f"\n  Statistics at {time_label}:")
        print(f"    Average flow: {np.mean(flows):.1f} vehicles")
        print(f"    Max flow: {np.max(flows):.1f} vehicles")
        print(f"    Active arcs: {sum(1 for f in flows if f > 0.1)}")
    
    # Create combined document
    print(f"\n{'='*60}")
    print("Creating combined document...")
    print(f"{'='*60}")
    
    combined = ["\\documentclass[12pt]{article}", "\\usepackage{tikz}", "\\usepackage[margin=1in]{geometry}",
                "\\usepackage{graphicx}", "", "\\begin{document}", "",
                "\\section*{Northern Italy Highway Network Traffic Patterns}", ""]
    
    for out in latex_outputs:
        combined.append(f"\\subsection*{{{out['time']} (Slot {out['slot']})}}")
        combined.append("\\begin{center}")
        combined.append(out['code'])
        combined.append("\\end{center}")
        combined.append("\\clearpage")
    
    combined.append("\\end{document}")
    
    with open("network_traffic_complete.tex", 'w', encoding='utf-8') as f:
        f.write("\n".join(combined))
    
    print("[OK] All visualizations generated with TIME-SPECIFIC data!")

if __name__ == "__main__":
    main()