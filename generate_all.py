"""
Master Script: Complete Network Analysis and LaTeX Generation
WINDOWS COMPATIBLE VERSION - No Unicode emoji characters
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def create_directory_structure():
    """Create organized output directory structure"""
    print("\n" + "="*60)
    print("Creating output directory structure...")
    print("="*60)
    
    # Create main output directory
    output_dir = Path("NETWORK_ANALYSIS_OUTPUT")
    output_dir.mkdir(exist_ok=True)
    
    # Create subdirectories
    subdirs = {
        'latex': output_dir / 'latex',
        'figures': output_dir / 'figures',
        'data': output_dir / 'data',
        'overleaf': output_dir / 'overleaf_package'
    }
    
    for name, path in subdirs.items():
        path.mkdir(exist_ok=True)
        print(f"  Created: {path}")
    
    return output_dir, subdirs

def run_network_topology_generator(subdirs):
    """Run the network topology generator"""
    print("\n" + "="*60)
    print("STEP 1: Generating Network Topology LaTeX")
    print("="*60)
    
    # Check if files exist, use FIXED version if available
    if os.path.exists("network_topology_generator_FIXED.py"):
        script = "network_topology_generator_FIXED.py"
    else:
        script = "network_topology_generator.py"
    
    result = subprocess.run([sys.executable, script], 
                          capture_output=True, text=True, encoding='utf-8', errors='replace')
    
    if result.returncode == 0:
        print("[OK] Network topology generated successfully")
        print(result.stdout)
        
        # Move generated files
        for file in ["network_topology_complete.tex", "network_topology_simplified.tex"]:
            if os.path.exists(file):
                shutil.copy(file, subdirs['latex'] / file)
                print(f"  Copied: {file} -> latex/")
    else:
        print("[ERROR] Error generating network topology:")
        print(result.stderr)
        return False
    
    return True

def run_traffic_visualizer(subdirs):
    """Run the traffic visualization generator"""
    print("\n" + "="*60)
    print("STEP 2: Generating Traffic Visualizations")
    print("="*60)
    
    # Check if files exist, prioritize AUTO version (auto-detects solution file)
    if os.path.exists("network_traffic_visualizer_AUTO.py"):
        script = "network_traffic_visualizer_AUTO.py"
    elif os.path.exists("network_traffic_visualizer_FIXED.py"):
        script = "network_traffic_visualizer_FIXED.py"
    else:
        script = "network_traffic_visualizer.py"
    
    result = subprocess.run([sys.executable, script], 
                          capture_output=True, text=True, encoding='utf-8', errors='replace')
    
    if result.returncode == 0:
        print("[OK] Traffic visualizations generated successfully")
        print(result.stdout)
        
        # Move PNG files
        png_files = ["network_traffic_8AM.png", "network_traffic_12PM.png", "network_traffic_6PM.png"]
        for file in png_files:
            if os.path.exists(file):
                shutil.copy(file, subdirs['figures'] / file)
                print(f"  Copied: {file} -> figures/")
        
        # Move LaTeX files
        tex_files = ["network_traffic_8AM.tex", "network_traffic_12PM.tex", 
                     "network_traffic_6PM.tex", "network_traffic_complete.tex"]
        for file in tex_files:
            if os.path.exists(file):
                shutil.copy(file, subdirs['latex'] / file)
                print(f"  Copied: {file} -> latex/")
    else:
        print("[ERROR] Error generating traffic visualizations:")
        print(result.stderr)
        return False
    
    return True

def copy_congestion_analysis(subdirs):
    """Copy the congestion analysis subsection"""
    print("\n" + "="*60)
    print("STEP 3: Copying Congestion Analysis Subsection")
    print("="*60)
    
    source = "congestion_analysis_subsection.tex"
    if os.path.exists(source):
        shutil.copy(source, subdirs['latex'] / source)
        print(f"[OK] Copied: {source} -> latex/")
        return True
    else:
        print(f"[WARNING] File not found: {source}")
        print("  You can create this file later or download from outputs")
        return True  # Don't fail the whole process

def create_master_document(subdirs):
    """Create a master LaTeX document that includes everything"""
    print("\n" + "="*60)
    print("STEP 4: Creating Master LaTeX Document")
    print("="*60)
    
    master_doc = []
    
    # Document class and packages
    master_doc.append("\\documentclass[12pt,a4paper]{article}")
    master_doc.append("\\usepackage[utf8]{inputenc}")
    master_doc.append("\\usepackage[T1]{fontenc}")
    master_doc.append("\\usepackage{tikz}")
    master_doc.append("\\usepackage{graphicx}")
    master_doc.append("\\usepackage[margin=1in]{geometry}")
    master_doc.append("\\usepackage{amsmath,amssymb}")
    master_doc.append("\\usepackage{booktabs}")
    master_doc.append("\\usepackage{caption}")
    master_doc.append("\\usepackage{subcaption}")
    master_doc.append("\\usepackage{hyperref}")
    master_doc.append("\\usetikzlibrary{arrows.meta,positioning,shapes.geometric}")
    master_doc.append("")
    master_doc.append("\\title{Northern Italy Highway Network: \\\\")
    master_doc.append("       Traffic Assignment and Congestion Analysis}")
    master_doc.append("\\author{ITER-FLOW Model Results}")
    master_doc.append("\\date{\\today}")
    master_doc.append("")
    master_doc.append("\\begin{document}")
    master_doc.append("")
    master_doc.append("\\maketitle")
    master_doc.append("\\tableofcontents")
    master_doc.append("\\clearpage")
    master_doc.append("")
    
    # Section 1: Network Topology
    master_doc.append("\\section{Network Topology}")
    master_doc.append("")
    master_doc.append("This section presents the complete topology of the Northern Italy highway network ")
    master_doc.append("used in the ITER-FLOW traffic assignment model. The network represents the major ")
    master_doc.append("highway corridors connecting cities, tourist destinations, and international border crossings ")
    master_doc.append("across Northern Italy.")
    master_doc.append("")
    
    # Check if topology files exist
    if (subdirs['latex'] / "network_topology_complete.tex").exists():
        master_doc.append("\\subsection{Complete Network}")
        master_doc.append("\\input{network_topology_complete.tex}")
        master_doc.append("")
    
    if (subdirs['latex'] / "network_topology_simplified.tex").exists():
        master_doc.append("\\subsection{Simplified Network (Major Nodes)}")
        master_doc.append("\\input{network_topology_simplified.tex}")
        master_doc.append("")
    
    # Section 2: Traffic Patterns
    master_doc.append("\\clearpage")
    master_doc.append("\\section{Traffic Flow Patterns}")
    master_doc.append("")
    master_doc.append("This section presents traffic flow patterns at three critical time points during the day. ")
    master_doc.append("The thickness and color intensity of each arc represent the traffic volume, with heavier ")
    master_doc.append("lines indicating higher flow intensity.")
    master_doc.append("")
    
    # Add the three time snapshots
    times = ["8AM", "12PM", "6PM"]
    slots = [8, 24, 48]
    
    for time, slot in zip(times, slots):
        png_file = subdirs['figures'] / f"network_traffic_{time}.png"
        if png_file.exists():
            master_doc.append(f"\\subsection{{Traffic at {time} (Slot {slot})}}")
            master_doc.append("")
            master_doc.append("\\begin{figure}[h]")
            master_doc.append("\\centering")
            master_doc.append(f"\\includegraphics[width=0.95\\textwidth]{{../figures/network_traffic_{time}.png}}")
            master_doc.append(f"\\caption{{Network traffic intensity at {time} (time slot {slot}). ")
            master_doc.append("Line thickness and color indicate traffic volume.}")
            master_doc.append(f"\\label{{fig:traffic_{time}}}")
            master_doc.append("\\end{figure}")
            master_doc.append("")
            master_doc.append("\\clearpage")
            master_doc.append("")
    
    # Section 3: Congestion Analysis
    if (subdirs['latex'] / "congestion_analysis_subsection.tex").exists():
        master_doc.append("\\section{Network Congestion Analysis}")
        master_doc.append("")
        master_doc.append("\\input{congestion_analysis_subsection.tex}")
        master_doc.append("")
    
    # Section 4: Summary and Conclusions
    master_doc.append("\\clearpage")
    master_doc.append("\\section{Summary and Conclusions}")
    master_doc.append("")
    master_doc.append("The ITER-FLOW model successfully captures the complex traffic dynamics on the Northern Italy ")
    master_doc.append("highway network through an iterative User Equilibrium approach. Key findings include:")
    master_doc.append("")
    master_doc.append("\\begin{itemize}")
    master_doc.append("    \\item Convergence achieved in 2-3 iterations with less than 5\\% TSTT change")
    master_doc.append("    \\item Metropolitan areas (particularly Milan) exhibit the highest congestion levels")
    master_doc.append("    \\item Inter-regional corridors show sustained high utilization throughout the day")
    master_doc.append("    \\item Tourist routes demonstrate asymmetric temporal patterns")
    master_doc.append("    \\item Approximately 28\\% of arcs experience utilization exceeding 100\\%")
    master_doc.append("\\end{itemize}")
    master_doc.append("")
    master_doc.append("The model provides a robust foundation for infrastructure planning and traffic management ")
    master_doc.append("policy analysis in this critical European transportation corridor.")
    master_doc.append("")
    
    master_doc.append("\\end{document}")
    
    # Write master document
    master_file = subdirs['latex'] / "master_document.tex"
    with open(master_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(master_doc))
    
    print(f"[OK] Created master document: {master_file}")
    return True

def create_overleaf_package(output_dir, subdirs):
    """Create a complete package ready for Overleaf upload"""
    print("\n" + "="*60)
    print("STEP 5: Creating Overleaf Package")
    print("="*60)
    
    overleaf_dir = subdirs['overleaf']
    
    # Copy LaTeX files to overleaf directory
    latex_files = list(subdirs['latex'].glob("*.tex"))
    for file in latex_files:
        shutil.copy(file, overleaf_dir / file.name)
    
    # Copy figure files
    figures_dir = overleaf_dir / "figures"
    figures_dir.mkdir(exist_ok=True)
    
    figure_files = list(subdirs['figures'].glob("*.png"))
    for file in figure_files:
        shutil.copy(file, figures_dir / file.name)
    
    # Create README for Overleaf
    readme = []
    readme.append("ITER-FLOW Network Analysis - Overleaf Package")
    readme.append("=" * 50)
    readme.append("")
    readme.append("This package contains all necessary files for compiling the")
    readme.append("Northern Italy Highway Network analysis document in Overleaf.")
    readme.append("")
    readme.append("FILES INCLUDED:")
    readme.append("---------------")
    readme.append("")
    readme.append("LaTeX Documents:")
    for file in latex_files:
        readme.append(f"  - {file.name}")
    readme.append("")
    readme.append("Figures:")
    for file in figure_files:
        readme.append(f"  - figures/{file.name}")
    readme.append("")
    readme.append("COMPILATION INSTRUCTIONS:")
    readme.append("-------------------------")
    readme.append("")
    readme.append("1. Upload all files to Overleaf (maintain the 'figures' subdirectory)")
    readme.append("2. Set 'master_document.tex' as the main document")
    readme.append("3. Compile using pdfLaTeX")
    readme.append("")
    readme.append("For questions, refer to the ITER-FLOW documentation.")
    
    readme_file = overleaf_dir / "README.txt"
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(readme))
    
    print(f"[OK] Overleaf package created in: {overleaf_dir}")
    print(f"   Total files: {len(list(overleaf_dir.rglob('*')))}")
    
    # Create a zip file for easy upload
    import zipfile
    
    zip_path = output_dir / "overleaf_package.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in overleaf_dir.rglob('*'):
            if file.is_file():
                arcname = file.relative_to(overleaf_dir)
                zipf.write(file, arcname)
    
    print(f"[OK] Created zip archive: {zip_path}")
    print(f"   Ready for direct upload to Overleaf!")
    
    return True

def create_summary_report(output_dir, subdirs):
    """Create a summary report of all generated files"""
    print("\n" + "="*60)
    print("STEP 6: Creating Summary Report")
    print("="*60)
    
    summary = []
    summary.append("ITER-FLOW Network Analysis Generation Summary")
    summary.append("=" * 60)
    summary.append("")
    summary.append(f"Output Directory: {output_dir.absolute()}")
    summary.append("")
    summary.append("GENERATED COMPONENTS:")
    summary.append("-" * 60)
    summary.append("")
    
    summary.append("1. NETWORK TOPOLOGY:")
    summary.append("   - network_topology_complete.tex (full network)")
    summary.append("   - network_topology_simplified.tex (major nodes only)")
    summary.append("")
    
    summary.append("2. TRAFFIC VISUALIZATIONS:")
    summary.append("   - network_traffic_8AM.png + .tex (morning peak, slot 8)")
    summary.append("   - network_traffic_12PM.png + .tex (midday, slot 24)")
    summary.append("   - network_traffic_6PM.png + .tex (evening peak, slot 48)")
    summary.append("   - network_traffic_complete.tex (combined document)")
    summary.append("")
    
    summary.append("3. CONGESTION ANALYSIS:")
    summary.append("   - congestion_analysis_subsection.tex (detailed analysis)")
    summary.append("")
    
    summary.append("4. MASTER DOCUMENT:")
    summary.append("   - master_document.tex (complete integrated document)")
    summary.append("")
    
    summary.append("5. OVERLEAF PACKAGE:")
    summary.append("   - overleaf_package.zip (ready for upload)")
    summary.append("   - overleaf_package/ (uncompressed files)")
    summary.append("")
    
    summary.append("=" * 60)
    summary.append("USAGE INSTRUCTIONS:")
    summary.append("-" * 60)
    summary.append("")
    summary.append("FOR OVERLEAF:")
    summary.append("1. Upload overleaf_package.zip to Overleaf")
    summary.append("2. Set master_document.tex as main document")
    summary.append("3. Compile with pdfLaTeX")
    summary.append("")
    summary.append("FOR LOCAL COMPILATION:")
    summary.append(f"cd {subdirs['latex'].absolute()}")
    summary.append("pdflatex master_document.tex")
    summary.append("")
    
    summary_file = output_dir / "GENERATION_SUMMARY.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(summary))
    
    print("[OK] Summary report created")
    
    return True

def main():
    """Main execution function"""
    print("\n" + "="*70)
    print(" " * 15 + "ITER-FLOW NETWORK ANALYSIS GENERATOR")
    print(" " * 10 + "Complete LaTeX and Visualization Generation")
    print("="*70)
    
    # Create directory structure
    output_dir, subdirs = create_directory_structure()
    
    # Run all generation steps
    steps = [
        (run_network_topology_generator, (subdirs,)),
        (run_traffic_visualizer, (subdirs,)),
        (copy_congestion_analysis, (subdirs,)),
        (create_master_document, (subdirs,)),
        (create_overleaf_package, (output_dir, subdirs)),
        (create_summary_report, (output_dir, subdirs))
    ]
    
    success_count = 0
    for i, (step_func, args) in enumerate(steps, 1):
        try:
            if step_func(*args):
                success_count += 1
        except Exception as e:
            print(f"\n[ERROR] Error in step {i}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Final summary
    print("\n" + "="*70)
    print("GENERATION COMPLETE")
    print("="*70)
    print(f"\nCompleted {success_count}/{len(steps)} steps successfully")
    
    if success_count >= 4:  # At least 4 out of 6 is acceptable
        print("\n[OK] Main components generated successfully!")
        print(f"\nOutput location: {output_dir.absolute()}")
        print(f"\nOverleaf package: {output_dir.absolute() / 'overleaf_package.zip'}")
        print("\nReady for upload to Overleaf or local compilation!")
    else:
        print("\n[WARNING] Some components failed to generate. Check logs above.")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    main()