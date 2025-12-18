import pandas as pd
import numpy as np
import os

# Configuration - MULTIPLE FILES
SCENARIOS = [
    {
        'file': "solution_ITERATIVE_UE_bench0_250_medium.xlsx",
        'label': "Naïve-0 baseline",
        'output_prefix': "bench0"
    },
    {
        'file': "solution_ITERATIVE_UE_MEDIUM_bench_random_250.xlsx",
        'label': "Random baseline",
        'output_prefix': "random"
    },
    {
        'file': "solution_ITERATIVE_UE_dataset_medium_traffic_250.xlsx",
        'label': "Optimization",
        'output_prefix': "optimization"
    }
]

# Congestion thresholds
GREEN_THRESHOLD = 50
ORANGE_THRESHOLD = 100
RED_THRESHOLD = 150

print("\n" + "="*70)
print("📊 GENERATING LATEX CODE FOR CONGESTION ANALYSIS")
print("="*70)

# Store all LaTeX code
latex_output = []

# Start figure environment
latex_output.append("\\begin{figure}[htbp]")
latex_output.append("\\centering")
latex_output.append("")

for idx, scenario in enumerate(SCENARIOS):
    INPUT_FILE = scenario['file']
    LABEL = scenario['label']
    PREFIX = scenario['output_prefix']
    
    print(f"\n{'='*70}")
    print(f"📁 Processing: {LABEL}")
    print(f"{'='*70}")
    
    if not os.path.exists(INPUT_FILE):
        print(f"   ⚠️  File not found: {INPUT_FILE}")
        continue
    
    # Load data
    print(f"\n📂 Loading data from: {INPUT_FILE}")
    df_arc_stats = pd.read_excel(INPUT_FILE, sheet_name="Arc_Statistics")
    
    utilizations = df_arc_stats['Max_Max_Util'].values
    
    # Count congestion levels
    green_count = np.sum(utilizations < GREEN_THRESHOLD)
    orange_count = np.sum((utilizations >= GREEN_THRESHOLD) & (utilizations < ORANGE_THRESHOLD))
    red_count = np.sum((utilizations >= ORANGE_THRESHOLD) & (utilizations < RED_THRESHOLD))
    purple_count = np.sum(utilizations >= RED_THRESHOLD)
    total_arcs = len(utilizations)
    
    over_capacity = np.sum(utilizations > 100)
    over_severe = np.sum(utilizations > 150)
    max_util = np.max(utilizations)
    mean_util = np.mean(utilizations)
    median_util = np.median(utilizations)
    
    print(f"   Total arcs: {total_arcs}")
    print(f"   Mean: {mean_util:.1f}%, Median: {median_util:.1f}%, Max: {max_util:.1f}%")
    print(f"   Green: {green_count}, Orange: {orange_count}, Red: {red_count}, Purple: {purple_count}")
    
    # Create histogram bins
    bin_max = np.ceil(max_util / 50) * 50
    bins = np.arange(0, bin_max + 5, 5)  # 5% bins
    hist, bin_edges = np.histogram(utilizations, bins=bins)
    
    # Start subfigure
    if idx > 0:
        latex_output.append("")
        latex_output.append("\\vspace{0.8cm}")
        latex_output.append("")
    
    latex_output.append(f"% ============ {LABEL.upper()} ============")
    latex_output.append("\\begin{subfigure}{\\textwidth}")
    latex_output.append("\\centering")
    latex_output.append("\\begin{tikzpicture}")
    latex_output.append("")
    
    # LEFT CHART - Categorical bars
    latex_output.append("% Left chart - Congestion Level Distribution")
    latex_output.append("\\begin{axis}[")
    latex_output.append(f"    name=left{idx+1},")
    latex_output.append("    at={(0,0)},")
    latex_output.append("    width=0.48\\textwidth,")
    latex_output.append("    height=0.4\\textwidth,")
    latex_output.append("    ybar,")
    latex_output.append("    bar width=40pt,")
    latex_output.append("    xlabel={Congestion Level},")
    latex_output.append("    ylabel={Number of Arcs},")
    latex_output.append("    ymin=0, ymax=200,")
    latex_output.append("    symbolic x coords={Green, Orange, Red, Purple},")
    latex_output.append("    xtick=data,")
    latex_output.append("    xticklabels={Green\\\\(0-50\\%), Orange\\\\(50-100\\%), Red\\\\(100-150\\%), Purple\\\\(>150\\%)},")
    latex_output.append("    x tick label style={align=center, font=\\small},")
    latex_output.append("    ymajorgrids=true,")
    latex_output.append("    grid style={dashed, gray!30},")
    latex_output.append("]")
    
    # Add bars
    latex_output.append("\\addplot[fill=green!60, draw=black, line width=1pt] coordinates {")
    latex_output.append(f"    (Green,{green_count}) (Orange,0) (Red,0) (Purple,0)")
    latex_output.append("};")
    latex_output.append("\\addplot[fill=orange!70, draw=black, line width=1pt] coordinates {")
    latex_output.append(f"    (Green,0) (Orange,{orange_count}) (Red,0) (Purple,0)")
    latex_output.append("};")
    latex_output.append("\\addplot[fill=red!70, draw=black, line width=1pt] coordinates {")
    latex_output.append(f"    (Green,0) (Orange,0) (Red,{red_count}) (Purple,0)")
    latex_output.append("};")
    latex_output.append("\\addplot[fill=violet!70, draw=black, line width=1pt] coordinates {")
    latex_output.append(f"    (Green,0) (Orange,0) (Red,0) (Purple,{purple_count})")
    latex_output.append("};")
    latex_output.append("")
    
    # Add labels
    green_pct = green_count/total_arcs*100
    orange_pct = orange_count/total_arcs*100
    red_pct = red_count/total_arcs*100
    purple_pct = purple_count/total_arcs*100
    
    latex_output.append(f"\\node at (axis cs:Green,{green_count}) [above, font=\\small] {{{green_count}\\\\({green_pct:.1f}\\%)}};")
    latex_output.append(f"\\node at (axis cs:Orange,{orange_count}) [above, font=\\small] {{{orange_count}\\\\({orange_pct:.1f}\\%)}};")
    latex_output.append(f"\\node at (axis cs:Red,{red_count}) [above, font=\\small] {{{red_count}\\\\({red_pct:.1f}\\%)}};")
    latex_output.append(f"\\node at (axis cs:Purple,{purple_count}) [above, font=\\small] {{{purple_count}\\\\({purple_pct:.1f}\\%)}};")
    latex_output.append("")
    
    # Total line
    latex_output.append(f"\\draw[gray, dotted, line width=1.5pt] (axis cs:Green,{total_arcs}) -- (axis cs:Purple,{total_arcs});")
    latex_output.append(f"\\node[anchor=south east, font=\\footnotesize, gray] at (rel axis cs:0.98,0.15) {{Total: {total_arcs}}};")
    latex_output.append("\\end{axis}")
    latex_output.append("")
    
    # RIGHT CHART - Histogram
    latex_output.append("% Right chart - Utilization Histogram")
    latex_output.append("\\begin{axis}[")
    latex_output.append(f"    at={{(left{idx+1}.east)}}, anchor=west, xshift=1cm,")  # FIXED: double braces
    latex_output.append("    width=0.48\\textwidth,")
    latex_output.append("    height=0.4\\textwidth,")
    latex_output.append("    ybar interval,")
    latex_output.append("    xlabel={Utilization (\\%)},")
    latex_output.append("    ylabel={Number of Arcs},")
    latex_output.append("    xmin=0, xmax=250,")
    latex_output.append("    ymin=0, ymax=100,")
    latex_output.append("    xtick={0,50,100,150,200,250},")
    latex_output.append("    ymajorgrids=true,")
    latex_output.append("    grid style={dashed, gray!30},")
    latex_output.append("]")
    latex_output.append("")
    
    # Green (0-50%)
    green_coords = []
    orange_coords = []
    red_coords = []
    purple_coords = []
    
    for i, count in enumerate(hist):
        bin_start = bin_edges[i]
        coord = f"    ({bin_start:.0f},{count})"
        if bin_start < GREEN_THRESHOLD:
            green_coords.append(coord)
        elif bin_start < ORANGE_THRESHOLD:
            orange_coords.append(coord)
        elif bin_start < RED_THRESHOLD:
            red_coords.append(coord)
        else:
            purple_coords.append(coord)
    
    # Close each range
    if green_coords:
        green_coords.append(f"    ({GREEN_THRESHOLD},0)")
    if orange_coords:
        orange_coords.append(f"    ({ORANGE_THRESHOLD},0)")
    if red_coords:
        red_coords.append(f"    ({RED_THRESHOLD},0)")
    if purple_coords:
        purple_coords.append(f"    ({bin_max:.0f},0)")
    
    # Output green
    latex_output.append("\\addplot[fill=green!60, draw=black!50, line width=0.3pt] coordinates {")
    latex_output.extend(green_coords)
    latex_output.append("};")
    
    # Output orange
    latex_output.append("\\addplot[fill=orange!70, draw=black!50, line width=0.3pt] coordinates {")
    latex_output.extend(orange_coords)
    latex_output.append("};")
    
    # Output red
    latex_output.append("\\addplot[fill=red!70, draw=black!50, line width=0.3pt] coordinates {")
    latex_output.extend(red_coords)
    latex_output.append("};")
    
    # Output purple
    latex_output.append("\\addplot[fill=violet!70, draw=black!50, line width=0.3pt] coordinates {")
    latex_output.extend(purple_coords)
    latex_output.append("};")
    latex_output.append("")
    
    # Threshold lines
    latex_output.append("\\draw[black, dashed, line width=1.5pt] (axis cs:50,0) -- (axis cs:50,100);")
    latex_output.append("\\draw[black, dashed, line width=1.5pt] (axis cs:100,0) -- (axis cs:100,100);")
    latex_output.append("\\draw[black, dashed, line width=1.5pt] (axis cs:150,0) -- (axis cs:150,100);")
    latex_output.append("")
    
    # Statistics box
    latex_output.append("\\node[anchor=north east, font=\\tiny, align=left, fill=orange!15, draw=black, inner sep=3pt]")
    latex_output.append("    at (rel axis cs:0.97,0.97) {")
    latex_output.append("    Low/Medium: 50\\%\\\\")
    latex_output.append("    Medium/High: 100\\%\\\\")
    latex_output.append("    High/Severe: 150\\%\\\\")
    latex_output.append(f"    Max: {max_util:.1f}\\%\\\\")
    latex_output.append(f"    Over 100\\%: {over_capacity} arcs\\\\")
    latex_output.append(f"    Over 150\\%: {over_severe} arcs")
    latex_output.append("};")
    latex_output.append("\\end{axis}")
    latex_output.append("\\end{tikzpicture}")
    latex_output.append(f"\\caption{{{LABEL} (Mean util: {mean_util:.1f}\\%, Median: {median_util:.1f}\\%)}}")
    latex_output.append("\\end{subfigure}")

# Close figure
latex_output.append("")
latex_output.append("\\caption{Arc utilization statistics for the 250 ID trip instance (medium traffic). Left panels show congestion level distribution. Right panels show detailed utilization histograms with 5\\% bins and dashed vertical lines marking congestion thresholds. The optimization achieves dramatically better distribution: only 60 arcs exceed 100\\% utilization (vs 195 for Naïve, 182 for Random) and just 18 arcs exceed 150\\% (vs 178 for Naïve, 152 for Random).}")
latex_output.append("\\label{fig:utilization_comparison}")
latex_output.append("\\end{figure}")

# Write to file
output_file = "congestion_latex_output.tex"
with open(output_file, 'w') as f:
    f.write('\n'.join(latex_output))

# Print everything to console
print("\n" + "="*70)
print("📋 COMPLETE LATEX CODE (also saved to congestion_latex_output.tex)")
print("="*70 + "\n")

for line in latex_output:
    print(line)

print("\n" + "="*70)
print("✅ Copy the code above and paste it into your LaTeX document!")
print("="*70)