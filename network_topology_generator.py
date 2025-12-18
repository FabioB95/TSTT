"""
Complete Network Topology Generator for LaTeX/Overleaf
Generates a comprehensive TikZ representation of the entire Northern Italy highway network
WINDOWS COMPATIBLE - No Unicode emoji characters
"""

import json
import numpy as np

def load_network_data():
    """Load nodes and edges from JSON files"""
    with open('dati/nodes.json', 'r', encoding='utf-8') as f:
        nodes_data = json.load(f)
    
    with open('dati/arcs_bidirectional.json', 'r', encoding='utf-8') as f:
        edges_data = json.load(f)
    
    return nodes_data, edges_data

def generate_complete_network_latex(nodes_data, edges_data):
    """
    Generate complete LaTeX TikZ code for the entire network
    Creates a professional, publication-ready figure
    """
    nodes = nodes_data['nodes']
    edges = edges_data['edges']
    
    # Find coordinate bounds for scaling
    lons = [float(n['lon']) for n in nodes]
    lats = [float(n['lat']) for n in nodes]
    lon_min, lon_max = min(lons), max(lons)
    lat_min, lat_max = min(lats), max(lats)
    
    # Scale factor (TikZ coordinates) - larger scale for detail
    scale_x = 20.0 / (lon_max - lon_min)
    scale_y = 20.0 / (lat_max - lat_min)
    
    def scale_coords(lon, lat):
        x = (lon - lon_min) * scale_x
        y = (lat - lat_min) * scale_y
        return x, y
    
    # Build complete LaTeX document
    latex = []
    
    # Document header
    latex.append("\\documentclass[12pt,a3paper]{article}")
    latex.append("\\usepackage{tikz}")
    latex.append("\\usepackage[margin=0.5in]{geometry}")
    latex.append("\\usepackage{graphicx}")
    latex.append("\\usetikzlibrary{arrows.meta,positioning,shapes.geometric}")
    latex.append("")
    latex.append("\\begin{document}")
    latex.append("")
    latex.append("\\section*{Northern Italy Highway Network Topology}")
    latex.append("")
    latex.append("This figure presents the complete topology of the Northern Italy highway network used ")
    latex.append("in the ITER-FLOW traffic assignment model. The network comprises:")
    latex.append("\\begin{itemize}")
    latex.append(f"  \\item {len(nodes)} nodes representing highway junctions, cities, and border crossings")
    latex.append(f"  \\item {len(edges)} bidirectional arcs representing highway segments")
    latex.append("  \\item Node categories: Border crossings (blue), tourist attractions (green), ")
    latex.append("        high demand areas (orange), and standard junctions (gray)")
    latex.append("\\end{itemize}")
    latex.append("")
    latex.append("\\begin{center}")
    latex.append("\\begin{tikzpicture}[scale=0.7, every node/.style={font=\\tiny}]")
    latex.append("")
    
    # Define styles
    latex.append("  % Define node and edge styles")
    latex.append("  \\tikzstyle{border}=[circle, fill=blue!70, inner sep=2pt, minimum size=8pt]")
    latex.append("  \\tikzstyle{tourist}=[circle, fill=green!70, inner sep=1.5pt, minimum size=6pt]")
    latex.append("  \\tikzstyle{highdemand}=[circle, fill=orange!70, inner sep=1.5pt, minimum size=6pt]")
    latex.append("  \\tikzstyle{normal}=[circle, fill=gray!50, inner sep=1pt, minimum size=4pt]")
    latex.append("  \\tikzstyle{highway}=[draw=black!60, line width=0.8pt]")
    latex.append("")
    
    # Draw all edges first (so they're behind nodes)
    latex.append("  % Highway network arcs")
    edge_count = 0
    for edge in edges:
        from_id = str(edge['from_node'])
        to_id = str(edge['to_node'])
        
        # Find node coordinates
        from_node = next((n for n in nodes if n['ID'] == from_id), None)
        to_node = next((n for n in nodes if n['ID'] == to_id), None)
        
        if not from_node or not to_node:
            continue
        
        x1, y1 = scale_coords(float(from_node['lon']), float(from_node['lat']))
        x2, y2 = scale_coords(float(to_node['lon']), float(to_node['lat']))
        
        latex.append(f"  \\draw[highway] ({x1:.2f},{y1:.2f}) -- ({x2:.2f},{y2:.2f});")
        edge_count += 1
    
    latex.append("")
    latex.append(f"  % Total arcs drawn: {edge_count}")
    latex.append("")
    
    # Draw all nodes
    latex.append("  % Network nodes")
    node_categories = {'border': 0, 'tourist': 0, 'highdemand': 0, 'normal': 0}
    
    for node in nodes:
        node_id = node['ID']
        x, y = scale_coords(float(node['lon']), float(node['lat']))
        name = node.get('name', node_id)
        
        # Determine node style based on category
        category = node.get('category', 'bassa_domanda')
        if 'estero' in category:
            node_style = "border"
            node_categories['border'] += 1
            label_important = True
        elif 'turistica' in category:
            node_style = "tourist"
            node_categories['tourist'] += 1
            label_important = True
        elif 'grande_domanda' in category:
            node_style = "highdemand"
            node_categories['highdemand'] += 1
            label_important = True
        else:
            node_style = "normal"
            node_categories['normal'] += 1
            label_important = False
        
        # Draw node
        latex.append(f"  \\node[{node_style}] ({node_id}) at ({x:.2f},{y:.2f}) {{}};")
        
        # Add label for important nodes
        if label_important:
            # Clean name for LaTeX
            clean_name = name.replace('_', ' ').replace('à', '\\`a').replace('è', '\\`e')
            clean_name = clean_name.replace('ì', '\\`i').replace('ò', '\\`o').replace('ù', '\\`u')
            latex.append(f"  \\node[above=1pt of {node_id}, font=\\tiny] {{{clean_name}}};")
    
    latex.append("")
    latex.append(f"  % Node count: Border={node_categories['border']}, "
                f"Tourist={node_categories['tourist']}, "
                f"HighDemand={node_categories['highdemand']}, "
                f"Normal={node_categories['normal']}")
    latex.append("")
    
    # Add legend
    latex.append("  % Legend")
    latex.append("  \\node[anchor=north west, draw=black, fill=white, align=left, font=\\footnotesize] at (0, 20) {")
    latex.append("    \\textbf{Network Legend} \\\\[2pt]")
    latex.append("    \\tikz\\node[border] {}; Border Crossing \\\\")
    latex.append("    \\tikz\\node[tourist] {}; Tourist Attraction \\\\")
    latex.append("    \\tikz\\node[highdemand] {}; High Demand Area \\\\")
    latex.append("    \\tikz\\node[normal] {}; Standard Junction \\\\[2pt]")
    latex.append("    \\tikz\\draw[highway] (0,0) -- (0.3,0); Highway Segment")
    latex.append("  };")
    latex.append("")
    
    # Add statistics box
    latex.append("  % Network Statistics")
    latex.append("  \\node[anchor=north east, draw=black, fill=white, align=left, font=\\footnotesize] at (20, 20) {")
    latex.append("    \\textbf{Network Statistics} \\\\[2pt]")
    latex.append(f"    Total Nodes: {len(nodes)} \\\\")
    latex.append(f"    Total Arcs: {edge_count} \\\\")
    latex.append(f"    Border Crossings: {node_categories['border']} \\\\")
    latex.append(f"    Tourist Nodes: {node_categories['tourist']} \\\\")
    latex.append(f"    High Demand: {node_categories['highdemand']} \\\\")
    latex.append(f"    Standard Junctions: {node_categories['normal']}")
    latex.append("  };")
    latex.append("")
    
    latex.append("\\end{tikzpicture}")
    latex.append("\\end{center}")
    latex.append("")
    latex.append("\\clearpage")
    latex.append("")
    
    # Add detailed node table
    latex.append("\\section*{Node Directory}")
    latex.append("")
    latex.append("\\begin{table}[h]")
    latex.append("\\centering")
    latex.append("\\small")
    latex.append("\\begin{tabular}{llllr}")
    latex.append("\\hline")
    latex.append("\\textbf{ID} & \\textbf{Name} & \\textbf{Category} & \\textbf{Coordinates} & \\textbf{Population} \\\\")
    latex.append("\\hline")
    
    for node in sorted(nodes, key=lambda n: n['ID']):
        node_id = node['ID']
        name = node.get('name', '').replace('_', ' ')
        category = node.get('category', '').replace('_', ' ')
        lat = node.get('lat', 0)
        lon = node.get('lon', 0)
        pop = node.get('population', 0)
        
        latex.append(f"{node_id} & {name} & {category} & ({lat:.2f}, {lon:.2f}) & {pop:,} \\\\")
    
    latex.append("\\hline")
    latex.append("\\end{tabular}")
    latex.append(f"\\caption{{Complete directory of all {len(nodes)} nodes in the network.}}")
    latex.append("\\end{table}")
    latex.append("")
    
    latex.append("\\end{document}")
    
    return "\n".join(latex)

def generate_simplified_network_latex(nodes_data, edges_data):
    """
    Generate a simplified version showing only major nodes and key highways
    Suitable for presentations and overview figures
    """
    nodes = nodes_data['nodes']
    edges = edges_data['edges']
    
    # Filter for major nodes only
    major_nodes = [n for n in nodes if n.get('category') in 
                   ['ingresso_estero', 'attrazione_turistica', 'grande_domanda']]
    major_node_ids = {n['ID'] for n in major_nodes}
    
    # Filter edges that connect major nodes
    major_edges = [e for e in edges if 
                   str(e['from_node']) in major_node_ids and 
                   str(e['to_node']) in major_node_ids]
    
    # Find coordinate bounds
    lons = [float(n['lon']) for n in major_nodes]
    lats = [float(n['lat']) for n in major_nodes]
    lon_min, lon_max = min(lons), max(lons)
    lat_min, lat_max = min(lats), max(lats)
    
    scale_x = 18.0 / (lon_max - lon_min)
    scale_y = 18.0 / (lat_max - lat_min)
    
    def scale_coords(lon, lat):
        x = (lon - lon_min) * scale_x
        y = (lat - lat_min) * scale_y
        return x, y
    
    latex = []
    latex.append("\\documentclass[12pt]{article}")
    latex.append("\\usepackage{tikz}")
    latex.append("\\usepackage[margin=1in]{geometry}")
    latex.append("\\usetikzlibrary{arrows.meta,positioning}")
    latex.append("")
    latex.append("\\begin{document}")
    latex.append("")
    latex.append("\\section*{Northern Italy Highway Network - Simplified View}")
    latex.append("")
    latex.append(f"Showing {len(major_nodes)} major nodes and {len(major_edges)} key highway connections.")
    latex.append("")
    latex.append("\\begin{center}")
    latex.append("\\begin{tikzpicture}[scale=0.9]")
    latex.append("")
    
    # Styles
    latex.append("  \\tikzstyle{border}=[circle, fill=blue!70, draw=black, inner sep=2pt, minimum size=10pt]")
    latex.append("  \\tikzstyle{tourist}=[circle, fill=green!70, draw=black, inner sep=2pt, minimum size=8pt]")
    latex.append("  \\tikzstyle{highdemand}=[circle, fill=orange!70, draw=black, inner sep=2pt, minimum size=8pt]")
    latex.append("  \\tikzstyle{highway}=[draw=black, line width=1.2pt]")
    latex.append("")
    
    # Draw edges
    latex.append("  % Major highway connections")
    for edge in major_edges:
        from_id = str(edge['from_node'])
        to_id = str(edge['to_node'])
        
        from_node = next((n for n in major_nodes if n['ID'] == from_id), None)
        to_node = next((n for n in major_nodes if n['ID'] == to_id), None)
        
        if not from_node or not to_node:
            continue
        
        x1, y1 = scale_coords(float(from_node['lon']), float(from_node['lat']))
        x2, y2 = scale_coords(float(to_node['lon']), float(to_node['lat']))
        
        latex.append(f"  \\draw[highway] ({x1:.2f},{y1:.2f}) -- ({x2:.2f},{y2:.2f});")
    
    latex.append("")
    
    # Draw nodes with labels
    latex.append("  % Major network nodes")
    for node in major_nodes:
        node_id = node['ID']
        x, y = scale_coords(float(node['lon']), float(node['lat']))
        name = node.get('name', node_id).replace('_', ' ')
        
        category = node.get('category', '')
        if 'estero' in category:
            node_style = "border"
        elif 'turistica' in category:
            node_style = "tourist"
        else:
            node_style = "highdemand"
        
        latex.append(f"  \\node[{node_style}] ({node_id}) at ({x:.2f},{y:.2f}) {{}};")
        latex.append(f"  \\node[above=2pt of {node_id}, font=\\small] {{{name}}};")
    
    latex.append("")
    latex.append("\\end{tikzpicture}")
    latex.append("\\end{center}")
    latex.append("")
    latex.append("\\end{document}")
    
    return "\n".join(latex)

def main():
    """Main execution function"""
    print("="*60)
    print("Network Topology LaTeX Generator")
    print("="*60)
    
    # Load data
    print("\nLoading network data...")
    nodes_data, edges_data = load_network_data()
    print(f"  Loaded {len(nodes_data['nodes'])} nodes")
    print(f"  Loaded {len(edges_data['edges'])} edges")
    
    # Generate complete network
    print("\nGenerating complete network LaTeX...")
    complete_latex = generate_complete_network_latex(nodes_data, edges_data)
    
    output_file = "network_topology_complete.tex"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(complete_latex)
    print(f"  Saved: {output_file}")
    
    # Generate simplified network
    print("\nGenerating simplified network LaTeX...")
    simplified_latex = generate_simplified_network_latex(nodes_data, edges_data)
    
    output_file = "network_topology_simplified.tex"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(simplified_latex)
    print(f"  Saved: {output_file}")
    
    print("\n[OK] Network topology files generated successfully!")
    print("\nGenerated files:")
    print("  - network_topology_complete.tex (full network with all nodes)")
    print("  - network_topology_simplified.tex (major nodes only)")
    print("\nTo compile with LaTeX:")
    print("  pdflatex network_topology_complete.tex")
    print("\nOr upload to Overleaf for online compilation.")

if __name__ == "__main__":
    main()