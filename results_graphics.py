"""
Visualization script for optimization results - PAPER VERSION
Processes all solution files and creates figures in PAPER folder
Author: Fabio :)
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Rectangle
import os
import glob
import re

# Output folder
OUTPUT_FOLDER = "PAPER"

def extract_file_info(filename):
    """
    Extract scenario info from filename.
    Examples:
        solution_ITERATIVE_UE_100_low -> (100, 'low', None)
        solution_ITERATIVE_UE_bench0_1000_medium -> (1000, 'medium', 'bench0')
        solution_ITERATIVE_UE_MEDIUM_bench_random_250 -> (250, 'MEDIUM', 'bench_random')
    """
    basename = os.path.basename(filename).replace('.xlsx', '')
    
    # Pattern 1: solution_ITERATIVE_UE_<trips>_<traffic>
    match1 = re.match(r'solution_ITERATIVE_UE_(\d+)_(no_traffic|low|medium|high)', basename)
    if match1:
        trips = match1.group(1)
        traffic = match1.group(2)
        return trips, traffic, None
    
    # Pattern 2: solution_ITERATIVE_UE_bench<N>_<trips>_<traffic>
    match2 = re.match(r'solution_ITERATIVE_UE_(bench\d+)_(\d+)_(no_traffic|low|medium|high)', basename)
    if match2:
        bench = match2.group(1)
        trips = match2.group(2)
        traffic = match2.group(3)
        return trips, traffic, bench
    
    # Pattern 3: solution_ITERATIVE_UE_<TRAFFIC>_bench_random_<trips>
    match3 = re.match(r'solution_ITERATIVE_UE_(\w+)_bench_random_(\d+)', basename)
    if match3:
        traffic = match3.group(1)
        trips = match3.group(2)
        return trips, traffic, 'bench_random'
    
    # Pattern 4: More flexible - extract numbers and traffic levels
    trips_match = re.search(r'_(\d+)_', basename) or re.search(r'_(\d+)$', basename)
    traffic_match = re.search(r'(no_traffic|low|medium|high|LOW|MEDIUM|HIGH)', basename, re.IGNORECASE)
    bench_match = re.search(r'(bench\w*)', basename)
    
    trips = trips_match.group(1) if trips_match else 'unknown'
    traffic = traffic_match.group(1).lower() if traffic_match else 'unknown'
    bench = bench_match.group(1) if bench_match else None
    
    return trips, traffic, bench


def get_output_prefix(filename):
    """
    Generate output filename prefix based on input file.
    """
    trips, traffic, bench = extract_file_info(filename)
    
    if bench:
        return f"{bench}_{trips}_{traffic}"
    else:
        return f"{trips}_{traffic}"


def plot_arc_statistics(df_arc_stats, output_prefix, output_folder):
    """
    Plot comprehensive arc statistics including utilization and travel time increases.
    """
    output_file = os.path.join(output_folder, f"{output_prefix}_arc_statistics.png")
    print(f"   Creating arc statistics plot: {output_file}")
    
    if df_arc_stats is None or df_arc_stats.empty:
        print("      No arc statistics available")
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    
    # 1. Average Flow Distribution
    ax = axes[0, 0]
    ax.hist(df_arc_stats['Ave_Ave_Flow'], bins=30, edgecolor='black', 
            alpha=0.7, color='blue')
    mean_val = df_arc_stats['Ave_Ave_Flow'].mean()
    ax.axvline(x=mean_val, color='red', linestyle='--', linewidth=2, 
               label=f'Mean: {mean_val:.2f}')
    ax.set_xlabel('Average Flow (vehicles)', fontsize=11)
    ax.set_ylabel('Frequency', fontsize=11)
    ax.set_title('Distribution of Average Arc Flows', fontsize=12, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 2. Average Utilization Distribution
    ax = axes[0, 1]
    ax.hist(df_arc_stats['Ave_Ave_Util'], bins=30, edgecolor='black', 
            alpha=0.7, color='green')
    mean_val = df_arc_stats['Ave_Ave_Util'].mean()
    ax.axvline(x=mean_val, color='red', linestyle='--', linewidth=2, 
               label=f'Mean: {mean_val:.2f}%')
    ax.axvline(x=50, color='orange', linestyle='--', linewidth=1, alpha=0.5)
    ax.axvline(x=80, color='darkred', linestyle='--', linewidth=1, alpha=0.5)
    ax.set_xlabel('Average Utilization (%)', fontsize=11)
    ax.set_ylabel('Frequency', fontsize=11)
    ax.set_title('Distribution of Average Arc Utilization', fontsize=12, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 3. Travel Time Increase Distribution
    ax = axes[1, 0]
    ax.hist(df_arc_stats['Ave_AumentoTTArco'], bins=30, edgecolor='black', 
            alpha=0.7, color='orange')
    mean_val = df_arc_stats['Ave_AumentoTTArco'].mean()
    ax.axvline(x=mean_val, color='red', linestyle='--', linewidth=2, 
               label=f'Mean: {mean_val:.2f} min')
    ax.set_xlabel('Average Travel Time Increase (min)', fontsize=11)
    ax.set_ylabel('Frequency', fontsize=11)
    ax.set_title('Distribution of Travel Time Increases', fontsize=12, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 4. Max Utilization Distribution
    ax = axes[1, 1]
    ax.hist(df_arc_stats['Max_Max_Util'], bins=30, edgecolor='black', 
            alpha=0.7, color='purple')
    mean_val = df_arc_stats['Max_Max_Util'].mean()
    ax.axvline(x=mean_val, color='red', linestyle='--', linewidth=2, 
               label=f'Mean: {mean_val:.2f}%')
    ax.axvline(x=80, color='darkred', linestyle='--', linewidth=2, alpha=0.5, 
               label='High congestion (80%)')
    ax.axvline(x=100, color='black', linestyle='-', linewidth=2, alpha=0.5, 
               label='Capacity')
    ax.set_xlabel('Maximum Utilization (%)', fontsize=11)
    ax.set_ylabel('Frequency', fontsize=11)
    ax.set_title('Distribution of Peak Arc Utilization', fontsize=12, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()


def plot_top_congested_arcs(df_arc_stats, output_prefix, output_folder, top_n=15):
    """
    Plot the top N most congested arcs based on average utilization.
    """
    output_file = os.path.join(output_folder, f"{output_prefix}_top_congested_arcs.png")
    print(f"   Creating top congested arcs plot: {output_file}")
    
    if df_arc_stats is None or df_arc_stats.empty:
        print("      No arc statistics available")
        return
    
    # Sort by average utilization and get top N
    df_top = df_arc_stats.nlargest(top_n, 'Ave_Ave_Util').copy()
    df_top['Arc_Label'] = df_top['From'] + ' → ' + df_top['To']
    
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    
    # 1. Bar chart of average utilization
    ax = axes[0]
    colors = ['red' if x > 80 else 'orange' if x > 50 else 'green' 
              for x in df_top['Ave_Ave_Util']]
    bars = ax.barh(df_top['Arc_Label'], df_top['Ave_Ave_Util'], color=colors, 
                   edgecolor='black', alpha=0.7)
    ax.axvline(x=50, color='orange', linestyle='--', linewidth=1, alpha=0.5, 
               label='Medium threshold (50%)')
    ax.axvline(x=80, color='red', linestyle='--', linewidth=1, alpha=0.5, 
               label='High threshold (80%)')
    ax.set_xlabel('Average Utilization (%)', fontsize=11)
    ax.set_ylabel('Arc', fontsize=11)
    ax.set_title(f'Top {top_n} Most Utilized Arcs (Average)', fontsize=12, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='x')
    
    # 2. Bar chart of travel time increase
    ax = axes[1]
    bars = ax.barh(df_top['Arc_Label'], df_top['Ave_AumentoTTArco'], 
                   color='coral', edgecolor='black', alpha=0.7)
    ax.set_xlabel('Average Travel Time Increase (min)', fontsize=11)
    ax.set_ylabel('Arc', fontsize=11)
    ax.set_title(f'Top {top_n} Most Congested Arcs (Travel Time Delay)', 
                 fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()


def plot_travel_time_distribution(df_assignments, output_prefix, output_folder):
    """
    Plot distribution of travel times comparing FF, effective, and actual.
    """
    output_file = os.path.join(output_folder, f"{output_prefix}_travel_time_distribution.png")
    print(f"   Creating travel time distribution plot: {output_file}")
    
    if df_assignments.empty:
        print("      No data available")
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Filter out zero assignments
    df_active = df_assignments[df_assignments['Vehicles_Assigned'] > 0.01].copy()
    
    if df_active.empty:
        print("      No active assignments found")
        return
    
    # 1. Free-flow vs Effective time
    ax = axes[0, 0]
    if 'FreeFlow_Time_min' in df_active.columns and 'Effective_Time_min' in df_active.columns:
        ax.scatter(df_active['FreeFlow_Time_min'], df_active['Effective_Time_min'], 
                   alpha=0.5, s=50, c='blue')
        max_time = max(df_active['FreeFlow_Time_min'].max(), df_active['Effective_Time_min'].max())
        ax.plot([0, max_time], [0, max_time], 'r--', linewidth=2, label='No congestion')
        ax.set_xlabel('Free-Flow Time (min)', fontsize=11)
        ax.set_ylabel('Effective Time (min)', fontsize=11)
        ax.set_title('Free-Flow vs Effective Travel Time', fontsize=12, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    # 2. Inconvenience distribution
    ax = axes[0, 1]
    if 'Inconvenience_PWL' in df_active.columns:
        ax.hist(df_active['Inconvenience_PWL'], bins=30, edgecolor='black', 
                alpha=0.7, color='green')
        ax.axvline(x=df_active['Inconvenience_PWL'].mean(), color='red', 
                   linestyle='--', linewidth=2, label=f'Mean: {df_active["Inconvenience_PWL"].mean():.3f}')
        ax.set_xlabel('Inconvenience Ratio', fontsize=11)
        ax.set_ylabel('Frequency', fontsize=11)
        ax.set_title('Distribution of Inconvenience Ratios', fontsize=12, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    # 3. Congestion factor by path
    ax = axes[1, 0]
    if 'FreeFlow_Time_min' in df_active.columns and 'TravelTime_PWL_min' in df_active.columns:
        df_active['Congestion_Factor'] = df_active['TravelTime_PWL_min'] / df_active['FreeFlow_Time_min']
        ax.hist(df_active['Congestion_Factor'], bins=30, edgecolor='black', 
                alpha=0.7, color='orange')
        ax.axvline(x=1.0, color='green', linestyle='--', linewidth=2, label='No delay')
        ax.axvline(x=df_active['Congestion_Factor'].mean(), color='red', 
                   linestyle='--', linewidth=2, label=f'Mean: {df_active["Congestion_Factor"].mean():.3f}')
        ax.set_xlabel('Congestion Factor (Actual/Free-Flow)', fontsize=11)
        ax.set_ylabel('Frequency', fontsize=11)
        ax.set_title('Distribution of Congestion Factors', fontsize=12, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    # 4. Departure time distribution
    ax = axes[1, 1]
    if 'Departure_Slot' in df_active.columns and 'Vehicles_Assigned' in df_active.columns:
        departure_dist = df_active.groupby('Departure_Slot')['Vehicles_Assigned'].sum()
        ax.bar(departure_dist.index, departure_dist.values, color='purple', alpha=0.7, edgecolor='black')
        ax.set_xlabel('Departure Time Slot', fontsize=11)
        ax.set_ylabel('Number of Vehicles', fontsize=11)
        ax.set_title('Distribution of Departures Over Time', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()


def plot_convergence(df_convergence, output_prefix, output_folder):
    """
    Plot convergence history showing TSTT evolution.
    """
    output_file = os.path.join(output_folder, f"{output_prefix}_convergence.png")
    print(f"   Creating convergence plot: {output_file}")
    
    if df_convergence is None or df_convergence.empty:
        print("      No convergence data available")
        return
    
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    
    # 1. TSTT evolution
    ax = axes[0]
    ax.plot(df_convergence['Iteration'], df_convergence['TSTT'], 
            marker='o', linewidth=2, markersize=8, color='blue')
    ax.set_xlabel('Iteration', fontsize=11)
    ax.set_ylabel('TSTT (Total System Travel Time)', fontsize=11)
    ax.set_title('Convergence: TSTT Evolution', fontsize=12, fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    # Add values on points
    for i, row in df_convergence.iterrows():
        ax.annotate(f'{row["TSTT"]:.0f}', 
                   xy=(row['Iteration'], row['TSTT']),
                   xytext=(5, 5), textcoords='offset points',
                   fontsize=9, alpha=0.7)
    
    # 2. Change percentage
    ax = axes[1]
    if len(df_convergence) > 1:
        df_changes = df_convergence[df_convergence['Change_%'] != 0]
        if not df_changes.empty:
            ax.bar(df_changes['Iteration'], df_changes['Change_%'], 
                   color='green', alpha=0.7, edgecolor='black')
            ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax.set_xlabel('Iteration', fontsize=11)
        ax.set_ylabel('Change from Previous (%)', fontsize=11)
        ax.set_title('Convergence: Iteration-to-Iteration Change', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()


def create_summary_report(df_summary, df_convergence, output_prefix, output_folder):
    """
    Create a text summary report of the optimization results.
    """
    output_file = os.path.join(output_folder, f"{output_prefix}_summary.txt")
    print(f"   Creating summary report: {output_file}")
    
    with open(output_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write(f"OPTIMIZATION RESULTS SUMMARY - {output_prefix}\n")
        f.write("=" * 80 + "\n\n")
        
        # Main metrics
        f.write("MAIN METRICS:\n")
        f.write("-" * 80 + "\n")
        for _, row in df_summary.iterrows():
            metric = row['Metric']
            value = row['Value']
            if isinstance(value, float):
                if 'Assignment' in metric or '%' in metric or 'Util' in metric:
                    f.write(f"  {metric:35s}: {value:12.2f}%\n")
                elif 'TSTT' in metric or 'Flow' in metric or 'Demand' in metric:
                    f.write(f"  {metric:35s}: {value:12,.2f}\n")
                else:
                    f.write(f"  {metric:35s}: {value:12.4f}\n")
            else:
                f.write(f"  {metric:35s}: {value:>12}\n")
        
        f.write("\n")
        
        # Convergence history if available
        if df_convergence is not None and not df_convergence.empty:
            f.write("CONVERGENCE HISTORY:\n")
            f.write("-" * 80 + "\n")
            f.write(f"{'Iteration':>12} {'TSTT':>18} {'Change %':>18}\n")
            f.write("-" * 80 + "\n")
            for _, row in df_convergence.iterrows():
                it = int(row['Iteration'])
                tstt = row['TSTT']
                change = row['Change_%']
                if change == 0.0:
                    f.write(f"{it:12d} {tstt:18,.2f} {'(initial)':>18}\n")
                else:
                    f.write(f"{it:12d} {tstt:18,.2f} {change:+17.2f}%\n")
        
        f.write("\n" + "=" * 80 + "\n")
        f.write("END OF REPORT\n")
        f.write("=" * 80 + "\n")


def process_single_file(filepath, output_folder):
    """
    Process a single Excel file and generate all visualizations.
    """
    print(f"\n{'='*70}")
    print(f"Processing: {os.path.basename(filepath)}")
    print(f"{'='*70}")
    
    output_prefix = get_output_prefix(filepath)
    print(f"   Output prefix: {output_prefix}")
    
    try:
        # Load data
        df_summary = pd.read_excel(filepath, sheet_name="Summary")
        df_assignments = pd.read_excel(filepath, sheet_name="Assignments")
        
        try:
            df_convergence = pd.read_excel(filepath, sheet_name="Convergence")
        except:
            df_convergence = None
        
        try:
            df_arc_stats = pd.read_excel(filepath, sheet_name="Arc_Statistics")
        except:
            df_arc_stats = None
        
        # Generate all plots
        plot_travel_time_distribution(df_assignments, output_prefix, output_folder)
        
        if df_convergence is not None:
            plot_convergence(df_convergence, output_prefix, output_folder)
        
        if df_arc_stats is not None:
            plot_arc_statistics(df_arc_stats, output_prefix, output_folder)
            plot_top_congested_arcs(df_arc_stats, output_prefix, output_folder)
        
        create_summary_report(df_summary, df_convergence, output_prefix, output_folder)
        
        print(f"   ✅ Successfully processed: {os.path.basename(filepath)}")
        return True
        
    except Exception as e:
        print(f"   ❌ Error processing {os.path.basename(filepath)}: {e}")
        return False


def main():
    """
    Main function to process all solution files.
    """
    print("\n" + "="*70)
    print("📊 PAPER FIGURE GENERATOR")
    print("="*70)
    
    # Create output folder
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    print(f"\n📁 Output folder: {OUTPUT_FOLDER}/")
    
    # Find all solution files
    patterns = [
        "solution_ITERATIVE_UE_*.xlsx",
        "solution_*.xlsx"
    ]
    
    all_files = set()
    for pattern in patterns:
        files = glob.glob(pattern)
        all_files.update(files)
    
    # Also check in uploads folder
    upload_patterns = [
        "/mnt/user-data/uploads/solution_ITERATIVE_UE_*.xlsx",
        "/mnt/user-data/uploads/solution_*.xlsx"
    ]
    for pattern in upload_patterns:
        files = glob.glob(pattern)
        all_files.update(files)
    
    if not all_files:
        print("\n❌ No solution files found!")
        print("   Looking for files matching: solution_ITERATIVE_UE_*.xlsx")
        print("   Please upload your Excel files or place them in the current directory.")
        return
    
    print(f"\n📋 Found {len(all_files)} file(s) to process:")
    for f in sorted(all_files):
        print(f"   - {os.path.basename(f)}")
    
    # Process each file
    success_count = 0
    failed_files = []
    
    for filepath in sorted(all_files):
        if process_single_file(filepath, OUTPUT_FOLDER):
            success_count += 1
        else:
            failed_files.append(os.path.basename(filepath))
    
    # Summary
    print("\n" + "="*70)
    print("📊 PROCESSING COMPLETE")
    print("="*70)
    print(f"\n   ✅ Successfully processed: {success_count}/{len(all_files)} files")
    
    if failed_files:
        print(f"   ❌ Failed files:")
        for f in failed_files:
            print(f"      - {f}")
    
    # List generated files
    generated_files = glob.glob(os.path.join(OUTPUT_FOLDER, "*"))
    if generated_files:
        print(f"\n📁 Generated {len(generated_files)} files in {OUTPUT_FOLDER}/:")
        for f in sorted(generated_files):
            print(f"   - {os.path.basename(f)}")


if __name__ == "__main__":
    main()