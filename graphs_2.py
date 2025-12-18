"""
PAPER FIGURE GENERATOR v2
==========================
1. Top 5-10% congested arcs comparison across traffic scenarios
2. Heatmaps of flow matrix (green/orange/red)
3. Cell count statistics per congestion level

Author: Fabio :)
"""

import os
import glob
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import Patch
import seaborn as sns
from collections import defaultdict

# ============================================================
# CONFIGURATION
# ============================================================
OUTPUT_FOLDER = "PAPER_HEAT+ARCS"
TOP_PERCENT = 10  # Top 10% most congested arcs

# Congestion thresholds (utilization %)
THRESH_LOW = 50      # Below this = green (low congestion)
THRESH_MEDIUM = 80   # Below this = orange (medium), above = red (high)

# Colors
COLOR_LOW = '#2ecc71'      # Green
COLOR_MEDIUM = '#f39c12'   # Orange  
COLOR_HIGH = '#e74c3c'     # Red

# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def extract_file_info(filename):
    """
    Extract scenario info from filename.
    Returns: (trips, traffic_level, benchmark)
    """
    basename = os.path.basename(filename).replace('.xlsx', '')
    
    # Pattern 1: solution_ITERATIVE_UE_<trips>_<traffic>
    match1 = re.match(r'solution_ITERATIVE_UE_(\d+)_(no_traffic|low|medium|high)', basename, re.IGNORECASE)
    if match1:
        return match1.group(1), match1.group(2).lower(), None
    
    # Pattern 2: solution_ITERATIVE_UE_bench<N>_<trips>_<traffic>
    match2 = re.match(r'solution_ITERATIVE_UE_(bench\d+)_(\d+)_(no_traffic|low|medium|high)', basename, re.IGNORECASE)
    if match2:
        return match2.group(2), match2.group(3).lower(), match2.group(1)
    
    # Pattern 3: solution_ITERATIVE_UE_<TRAFFIC>_bench_random_<trips>
    match3 = re.match(r'solution_ITERATIVE_UE_(\w+)_bench_random_(\d+)', basename, re.IGNORECASE)
    if match3:
        return match3.group(2), match3.group(1).lower(), 'bench_random'
    
    # Pattern 4: dataset naming - solution_ITERATIVE_UE_dataset_<traffic>_<trips>
    match4 = re.match(r'solution_ITERATIVE_UE_dataset_(no_traffic|low|medium|high)_(\d+)', basename, re.IGNORECASE)
    if match4:
        return match4.group(2), match4.group(1).lower(), 'dataset'
    
    # Fallback: extract what we can
    trips_match = re.search(r'(\d+)', basename)
    traffic_match = re.search(r'(no_traffic|low|medium|high)', basename, re.IGNORECASE)
    
    trips = trips_match.group(1) if trips_match else 'unknown'
    traffic = traffic_match.group(1).lower() if traffic_match else 'unknown'
    
    return trips, traffic, None


def get_output_prefix(filename):
    """Generate output filename prefix."""
    trips, traffic, bench = extract_file_info(filename)
    if bench:
        return f"{bench}_{trips}_{traffic}"
    return f"{trips}_{traffic}"


def load_excel_data(filepath):
    """Load all sheets from Excel file."""
    try:
        df_summary = pd.read_excel(filepath, sheet_name="Summary")
        df_arc_stats = pd.read_excel(filepath, sheet_name="Arc_Statistics")
        
        try:
            df_assignments = pd.read_excel(filepath, sheet_name="Assignments")
        except:
            df_assignments = pd.DataFrame()
        
        try:
            df_convergence = pd.read_excel(filepath, sheet_name="Convergence")
        except:
            df_convergence = pd.DataFrame()
        
        return {
            'summary': df_summary,
            'arc_stats': df_arc_stats,
            'assignments': df_assignments,
            'convergence': df_convergence
        }
    except Exception as e:
        print(f"   Error loading {filepath}: {e}")
        return None


def classify_congestion(util):
    """Classify utilization into congestion level."""
    if util < THRESH_LOW:
        return 'low'
    elif util < THRESH_MEDIUM:
        return 'medium'
    else:
        return 'high'


def get_congestion_color(util):
    """Get color based on utilization."""
    if util < THRESH_LOW:
        return COLOR_LOW
    elif util < THRESH_MEDIUM:
        return COLOR_MEDIUM
    else:
        return COLOR_HIGH


# ============================================================
# FIGURE 1: TOP CONGESTED ARCS COMPARISON (3 SCENARIOS)
# ============================================================

def plot_top_congested_comparison(files_by_scenario, trips_count, output_folder):
    """
    Compare top 5-10% congested arcs across traffic scenarios.
    Shows travel time increase on congested arcs.
    """
    scenarios = ['no_traffic', 'low', 'medium', 'high']
    available_scenarios = [s for s in scenarios if s in files_by_scenario]
    
    if len(available_scenarios) < 2:
        print(f"   Need at least 2 scenarios for comparison, found: {available_scenarios}")
        return
    
    print(f"\n📊 Creating top congested arcs comparison for {trips_count} trips...")
    print(f"   Scenarios: {available_scenarios}")
    
    # Load data for each scenario
    scenario_data = {}
    all_arcs = set()
    
    for scenario in available_scenarios:
        filepath = files_by_scenario[scenario]
        data = load_excel_data(filepath)
        if data is None:
            continue
        
        df = data['arc_stats'].copy()
        df['Arc'] = df['From'] + ' → ' + df['To']
        scenario_data[scenario] = df
        all_arcs.update(df['Arc'].tolist())
    
    if not scenario_data:
        print("   No valid data loaded")
        return
    
    # Find top congested arcs (union across scenarios)
    # Use Ave_Ave_Util or Max_Max_Util for ranking
    combined_util = defaultdict(list)
    for scenario, df in scenario_data.items():
        for _, row in df.iterrows():
            arc = row['Arc']
            combined_util[arc].append(row['Max_Max_Util'])
    
    # Calculate max utilization across scenarios for each arc
    arc_max_util = {arc: max(utils) for arc, utils in combined_util.items()}
    
    # Get top N% arcs
    n_arcs = len(arc_max_util)
    n_top = max(5, int(n_arcs * TOP_PERCENT / 100))
    
    top_arcs = sorted(arc_max_util.keys(), key=lambda x: arc_max_util[x], reverse=True)[:n_top]
    
    print(f"   Total arcs: {n_arcs}, showing top {n_top} ({TOP_PERCENT}%)")
    
    # ---- FIGURE: Travel Time Increase Comparison ----
    fig, axes = plt.subplots(1, 2, figsize=(16, 8))
    
    # Subplot 1: Bar chart of travel time increase
    ax = axes[0]
    x = np.arange(len(top_arcs))
    width = 0.8 / len(available_scenarios)
    
    colors = {'no_traffic': '#3498db', 'low': '#2ecc71', 'medium': '#f39c12', 'high': '#e74c3c'}
    
    for i, scenario in enumerate(available_scenarios):
        df = scenario_data[scenario]
        tt_increases = []
        for arc in top_arcs:
            row = df[df['Arc'] == arc]
            if not row.empty:
                tt_increases.append(row['Ave_AumentoTTArco'].values[0])
            else:
                tt_increases.append(0)
        
        offset = (i - len(available_scenarios)/2 + 0.5) * width
        bars = ax.bar(x + offset, tt_increases, width, label=scenario.replace('_', ' ').title(),
                     color=colors.get(scenario, 'gray'), alpha=0.8, edgecolor='black', linewidth=0.5)
    
    ax.set_xlabel('Arc', fontsize=12)
    ax.set_ylabel('Travel Time Increase (min)', fontsize=12)
    ax.set_title(f'Top {TOP_PERCENT}% Congested Arcs - Travel Time Delay\n({trips_count} trips)', 
                 fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([a.replace(' → ', '\n→\n') for a in top_arcs], fontsize=8, rotation=45, ha='right')
    ax.legend(title='Traffic Scenario')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Subplot 2: Utilization comparison
    ax = axes[1]
    
    for i, scenario in enumerate(available_scenarios):
        df = scenario_data[scenario]
        utils = []
        for arc in top_arcs:
            row = df[df['Arc'] == arc]
            if not row.empty:
                utils.append(row['Max_Max_Util'].values[0])
            else:
                utils.append(0)
        
        offset = (i - len(available_scenarios)/2 + 0.5) * width
        bars = ax.bar(x + offset, utils, width, label=scenario.replace('_', ' ').title(),
                     color=colors.get(scenario, 'gray'), alpha=0.8, edgecolor='black', linewidth=0.5)
    
    # Add threshold lines
    ax.axhline(y=THRESH_LOW, color=COLOR_LOW, linestyle='--', linewidth=2, alpha=0.7, label=f'Low threshold ({THRESH_LOW}%)')
    ax.axhline(y=THRESH_MEDIUM, color=COLOR_MEDIUM, linestyle='--', linewidth=2, alpha=0.7, label=f'Medium threshold ({THRESH_MEDIUM}%)')
    ax.axhline(y=100, color=COLOR_HIGH, linestyle='-', linewidth=2, alpha=0.7, label='Capacity (100%)')
    
    ax.set_xlabel('Arc', fontsize=12)
    ax.set_ylabel('Max Utilization (%)', fontsize=12)
    ax.set_title(f'Top {TOP_PERCENT}% Congested Arcs - Peak Utilization\n({trips_count} trips)', 
                 fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([a.replace(' → ', '\n→\n') for a in top_arcs], fontsize=8, rotation=45, ha='right')
    ax.legend(title='Traffic Scenario', loc='upper right', fontsize=9)
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    output_file = os.path.join(output_folder, f"comparison_top_congested_{trips_count}.png")
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"   ✅ Saved: {output_file}")
    
    # ---- FIGURE: Line plot showing congestion evolution ----
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Sort arcs by average utilization across scenarios
    for scenario in available_scenarios:
        df = scenario_data[scenario]
        df_sorted = df.sort_values('Max_Max_Util', ascending=False).head(n_top * 2)
        
        ax.plot(range(len(df_sorted)), df_sorted['Max_Max_Util'].values, 
                marker='o', markersize=4, label=scenario.replace('_', ' ').title(),
                color=colors.get(scenario, 'gray'), alpha=0.8, linewidth=2)
    
    ax.axhline(y=THRESH_LOW, color=COLOR_LOW, linestyle='--', linewidth=2, alpha=0.5)
    ax.axhline(y=THRESH_MEDIUM, color=COLOR_MEDIUM, linestyle='--', linewidth=2, alpha=0.5)
    ax.axhline(y=100, color=COLOR_HIGH, linestyle='-', linewidth=2, alpha=0.5)
    
    ax.set_xlabel('Arc Rank (sorted by utilization)', fontsize=12)
    ax.set_ylabel('Max Utilization (%)', fontsize=12)
    ax.set_title(f'Arc Utilization Profile by Traffic Scenario\n({trips_count} trips)', 
                 fontsize=14, fontweight='bold')
    ax.legend(title='Traffic Scenario')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_file = os.path.join(output_folder, f"comparison_utilization_profile_{trips_count}.png")
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"   ✅ Saved: {output_file}")


# ============================================================
# FIGURE 2: HEATMAP OF FLOW MATRIX
# ============================================================

def create_flow_heatmap(filepath, output_folder):
    """
    Create heatmap of arc utilization with green/orange/red coloring.
    """
    output_prefix = get_output_prefix(filepath)
    print(f"\n📊 Creating heatmap for {output_prefix}...")
    
    data = load_excel_data(filepath)
    if data is None:
        return None
    
    df = data['arc_stats'].copy()
    
    # Get unique nodes
    all_nodes = sorted(set(df['From'].tolist() + df['To'].tolist()))
    n_nodes = len(all_nodes)
    node_to_idx = {node: i for i, node in enumerate(all_nodes)}
    
    # Create utilization matrix
    util_matrix = np.zeros((n_nodes, n_nodes))
    util_matrix[:] = np.nan  # NaN for non-existent arcs
    
    for _, row in df.iterrows():
        i = node_to_idx[row['From']]
        j = node_to_idx[row['To']]
        util_matrix[i, j] = row['Max_Max_Util']
    
    # Create custom colormap (green -> orange -> red)
    colors_list = [COLOR_LOW, COLOR_MEDIUM, COLOR_HIGH]
    n_bins = 100
    cmap = mcolors.LinearSegmentedColormap.from_list('congestion', colors_list, N=n_bins)
    
    # Set color bounds
    vmin, vmax = 0, 120  # Allow some overflow above 100%
    
    # Create figure
    fig, ax = plt.subplots(figsize=(14, 12))
    
    # Mask NaN values
    masked_matrix = np.ma.masked_invalid(util_matrix)
    
    # Plot heatmap
    im = ax.imshow(masked_matrix, cmap=cmap, vmin=vmin, vmax=vmax, aspect='auto')
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label('Max Utilization (%)', fontsize=12)
    
    # Add threshold indicators on colorbar
    cbar.ax.axhline(y=THRESH_LOW/vmax, color='white', linestyle='--', linewidth=2)
    cbar.ax.axhline(y=THRESH_MEDIUM/vmax, color='white', linestyle='--', linewidth=2)
    
    # Set ticks
    if n_nodes <= 30:
        ax.set_xticks(range(n_nodes))
        ax.set_yticks(range(n_nodes))
        ax.set_xticklabels(all_nodes, rotation=90, fontsize=8)
        ax.set_yticklabels(all_nodes, fontsize=8)
    else:
        # Too many nodes, show subset
        step = max(1, n_nodes // 20)
        ax.set_xticks(range(0, n_nodes, step))
        ax.set_yticks(range(0, n_nodes, step))
        ax.set_xticklabels([all_nodes[i] for i in range(0, n_nodes, step)], rotation=90, fontsize=7)
        ax.set_yticklabels([all_nodes[i] for i in range(0, n_nodes, step)], fontsize=7)
    
    ax.set_xlabel('To Node', fontsize=12)
    ax.set_ylabel('From Node', fontsize=12)
    ax.set_title(f'Arc Utilization Heatmap\n{output_prefix}', fontsize=14, fontweight='bold')
    
    # Add legend for congestion levels
    legend_elements = [
        Patch(facecolor=COLOR_LOW, label=f'Low (<{THRESH_LOW}%)'),
        Patch(facecolor=COLOR_MEDIUM, label=f'Medium ({THRESH_LOW}-{THRESH_MEDIUM}%)'),
        Patch(facecolor=COLOR_HIGH, label=f'High (>{THRESH_MEDIUM}%)')
    ]
    ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.15, 1))
    
    plt.tight_layout()
    output_file = os.path.join(output_folder, f"{output_prefix}_heatmap.png")
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"   ✅ Saved: {output_file}")
    
    # Count cells by congestion level
    valid_cells = masked_matrix.compressed()  # Remove NaN
    counts = {
        'low': np.sum(valid_cells < THRESH_LOW),
        'medium': np.sum((valid_cells >= THRESH_LOW) & (valid_cells < THRESH_MEDIUM)),
        'high': np.sum(valid_cells >= THRESH_MEDIUM),
        'total': len(valid_cells)
    }
    
    return counts


# ============================================================
# FIGURE 3: CONGESTION CELL COUNT SUMMARY
# ============================================================

def create_congestion_count_summary(all_counts, output_folder):
    """
    Create bar chart summarizing congestion cell counts across all files.
    """
    if not all_counts:
        print("   No data for congestion count summary")
        return
    
    print(f"\n📊 Creating congestion count summary...")
    
    # Prepare data
    scenarios = list(all_counts.keys())
    low_counts = [all_counts[s]['low'] for s in scenarios]
    medium_counts = [all_counts[s]['medium'] for s in scenarios]
    high_counts = [all_counts[s]['high'] for s in scenarios]
    
    # Create stacked bar chart
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # Subplot 1: Absolute counts
    ax = axes[0]
    x = np.arange(len(scenarios))
    width = 0.6
    
    ax.bar(x, low_counts, width, label=f'Low (<{THRESH_LOW}%)', color=COLOR_LOW, edgecolor='black')
    ax.bar(x, medium_counts, width, bottom=low_counts, label=f'Medium ({THRESH_LOW}-{THRESH_MEDIUM}%)', 
           color=COLOR_MEDIUM, edgecolor='black')
    ax.bar(x, high_counts, width, bottom=[l+m for l,m in zip(low_counts, medium_counts)], 
           label=f'High (>{THRESH_MEDIUM}%)', color=COLOR_HIGH, edgecolor='black')
    
    ax.set_xlabel('Scenario', fontsize=12)
    ax.set_ylabel('Number of Arcs', fontsize=12)
    ax.set_title('Arc Congestion Distribution (Absolute)', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([s.replace('_', '\n') for s in scenarios], fontsize=9)
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    # Subplot 2: Percentages
    ax = axes[1]
    totals = [all_counts[s]['total'] for s in scenarios]
    low_pct = [100*l/t if t > 0 else 0 for l, t in zip(low_counts, totals)]
    medium_pct = [100*m/t if t > 0 else 0 for m, t in zip(medium_counts, totals)]
    high_pct = [100*h/t if t > 0 else 0 for h, t in zip(high_counts, totals)]
    
    ax.bar(x, low_pct, width, label=f'Low (<{THRESH_LOW}%)', color=COLOR_LOW, edgecolor='black')
    ax.bar(x, medium_pct, width, bottom=low_pct, label=f'Medium ({THRESH_LOW}-{THRESH_MEDIUM}%)', 
           color=COLOR_MEDIUM, edgecolor='black')
    ax.bar(x, high_pct, width, bottom=[l+m for l,m in zip(low_pct, medium_pct)], 
           label=f'High (>{THRESH_MEDIUM}%)', color=COLOR_HIGH, edgecolor='black')
    
    ax.set_xlabel('Scenario', fontsize=12)
    ax.set_ylabel('Percentage of Arcs (%)', fontsize=12)
    ax.set_title('Arc Congestion Distribution (Percentage)', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([s.replace('_', '\n') for s in scenarios], fontsize=9)
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_ylim(0, 100)
    
    plt.tight_layout()
    output_file = os.path.join(output_folder, "congestion_count_summary.png")
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"   ✅ Saved: {output_file}")
    
    # Also create detailed table
    create_congestion_table(all_counts, output_folder)


def create_congestion_table(all_counts, output_folder):
    """Create Excel/CSV table of congestion counts."""
    rows = []
    for scenario, counts in all_counts.items():
        total = counts['total']
        rows.append({
            'Scenario': scenario,
            'Total_Arcs': total,
            'Low_Count': counts['low'],
            'Low_%': round(100*counts['low']/total, 2) if total > 0 else 0,
            'Medium_Count': counts['medium'],
            'Medium_%': round(100*counts['medium']/total, 2) if total > 0 else 0,
            'High_Count': counts['high'],
            'High_%': round(100*counts['high']/total, 2) if total > 0 else 0,
        })
    
    df = pd.DataFrame(rows)
    
    # Save as Excel
    output_file = os.path.join(output_folder, "congestion_counts.xlsx")
    df.to_excel(output_file, index=False)
    print(f"   ✅ Saved: {output_file}")
    
    # Also save as CSV
    output_file_csv = os.path.join(output_folder, "congestion_counts.csv")
    df.to_csv(output_file_csv, index=False)
    print(f"   ✅ Saved: {output_file_csv}")
    
    return df


# ============================================================
# MAIN FUNCTION
# ============================================================

def find_all_solution_files():
    """Find all solution Excel files."""
    patterns = [
        "solution_ITERATIVE_UE_*.xlsx",
        "solution_*.xlsx",
        "/mnt/user-data/uploads/solution_ITERATIVE_UE_*.xlsx",
        "/mnt/user-data/uploads/solution_*.xlsx",
    ]
    
    all_files = set()
    for pattern in patterns:
        files = glob.glob(pattern)
        all_files.update(files)
    
    return sorted(all_files)


def group_files_by_trips(files):
    """Group files by trip count for comparison."""
    groups = defaultdict(dict)
    
    for filepath in files:
        trips, traffic, bench = extract_file_info(filepath)
        key = f"{bench}_{trips}" if bench else trips
        groups[key][traffic] = filepath
    
    return groups


def main():
    """Main function."""
    print("\n" + "="*70)
    print("📊 PAPER FIGURE GENERATOR v2")
    print("="*70)
    
    # Create output folder
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    print(f"\n📁 Output folder: {OUTPUT_FOLDER}/")
    
    # Find all files
    all_files = find_all_solution_files()
    
    if not all_files:
        print("\n❌ No solution files found!")
        print("   Looking for: solution_ITERATIVE_UE_*.xlsx")
        print("   Please upload your Excel files.")
        return
    
    print(f"\n📋 Found {len(all_files)} file(s):")
    for f in all_files:
        print(f"   - {os.path.basename(f)}")
    
    # ============================================================
    # GENERATE HEATMAPS AND COLLECT COUNTS
    # ============================================================
    print("\n" + "="*70)
    print("GENERATING HEATMAPS")
    print("="*70)
    
    all_counts = {}
    for filepath in all_files:
        prefix = get_output_prefix(filepath)
        counts = create_flow_heatmap(filepath, OUTPUT_FOLDER)
        if counts:
            all_counts[prefix] = counts
    
    # ============================================================
    # GENERATE CONGESTION COUNT SUMMARY
    # ============================================================
    print("\n" + "="*70)
    print("GENERATING CONGESTION SUMMARY")
    print("="*70)
    
    create_congestion_count_summary(all_counts, OUTPUT_FOLDER)
    
    # ============================================================
    # GENERATE COMPARISON PLOTS (BY TRIP COUNT)
    # ============================================================
    print("\n" + "="*70)
    print("GENERATING SCENARIO COMPARISONS")
    print("="*70)
    
    groups = group_files_by_trips(all_files)
    
    for trips_key, files_by_scenario in groups.items():
        if len(files_by_scenario) >= 2:
            plot_top_congested_comparison(files_by_scenario, trips_key, OUTPUT_FOLDER)
        else:
            print(f"\n   Skipping {trips_key}: only {len(files_by_scenario)} scenario(s)")
    
    # ============================================================
    # FINAL SUMMARY
    # ============================================================
    print("\n" + "="*70)
    print("✅ ALL FIGURES GENERATED")
    print("="*70)
    
    generated = glob.glob(os.path.join(OUTPUT_FOLDER, "*"))
    print(f"\n📁 Generated {len(generated)} files in {OUTPUT_FOLDER}/:")
    for f in sorted(generated):
        print(f"   - {os.path.basename(f)}")


if __name__ == "__main__":
    main()