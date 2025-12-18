"""
SCRIPT MASTER - ANALISI COMPLETA AUTOMATICA
Esegue tutti gli step dell'analisi in sequenza
"""

import sys
import os
from datetime import datetime

print("="*80)
print("🚀 ANALISI COMPLETA AUTOMATICA - 250 TRIP")
print("="*80)
print(f"Inizio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

# ============================================================================
# CHECK PRELIMINARI
# ============================================================================
print("\n🔍 STEP 0: Controlli preliminari...")
print("-" * 80)

required_files = [
    "solution_ITERATIVE_UE_dataset_medium_traffic_250.xlsx",
    "INPUT_DATASETS/MEDIUM/OTT/dataset_medium_traffic_250.xlsx"
]

missing_files = []
for f in required_files:
    if os.path.exists(f):
        print(f"✓ {f}")
    else:
        print(f"✗ {f} - MANCANTE!")
        missing_files.append(f)

if missing_files:
    print(f"\n❌ File mancanti: {len(missing_files)}")
    print("Per favore, assicurati di avere tutti i file necessari.")
    sys.exit(1)

print("\n✅ Tutti i file necessari sono presenti!")

# ============================================================================
# STEP 1: ANALISI BATCH (250 trip)
# ============================================================================
print("\n" + "="*80)
print("📊 STEP 1: Analisi batch di tutti i 250 trip")
print("="*80)
print("Questo step genererà:")
print("  - Statistiche aggregate (convergenza, domanda, congestione)")
print("  - 250 grafici individuali per ogni trip")
print("  - Report riassuntivo testuale")
print("\nTempo stimato: 3-5 minuti")
print("-" * 80)

try:
    import subprocess
    result = subprocess.run([sys.executable, "analyze_all_250_trips.py"], 
                          capture_output=True, text=True)
    print(result.stdout)
    if result.returncode == 0:
        print("\n✅ STEP 1 COMPLETATO!")
    else:
        print(f"\n❌ ERRORE nello Step 1: {result.stderr}")
        print("Continuo con gli step successivi...")
except Exception as e:
    print(f"\n❌ ERRORE nello Step 1: {str(e)}")
    print("Continuo con gli step successivi...")

# ============================================================================
# STEP 2: ANALISI PERCORSI E ARCHI IN COMUNE
# ============================================================================
print("\n" + "="*80)
print("🗺️  STEP 2: Analisi rete e percorsi con archi in comune")
print("="*80)
print("Questo step genererà:")
print("  - Grafo della rete con archi condivisi evidenziati")
print("  - Statistiche sharing degli archi")
print("  - Excel con dettagli completi")
print("  - Visualizzazioni percorsi per trip esempio")
print("\nTempo stimato: 2-3 minuti")
print("-" * 80)

try:
    result = subprocess.run([sys.executable, "complete_path_analysis.py"],
                          capture_output=True, text=True)
    print(result.stdout)
    if result.returncode == 0:
        print("\n✅ STEP 2 COMPLETATO!")
    else:
        print(f"\n❌ ERRORE nello Step 2: {result.stderr}")
        print("Continuo con lo step successivo...")
except Exception as e:
    print(f"\n❌ ERRORE nello Step 2: {str(e)}")
    print("Continuo con lo step successivo...")

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print("\n" + "="*80)
print("🎉 ANALISI COMPLETA TERMINATA!")
print("="*80)
print(f"Fine: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()
print("📂 OUTPUT GENERATI:")
print()
print("1. /mnt/user-data/outputs/ANALYSIS_250_TRIPS/")
print("   └── summary_stats/        (4 grafici aggregati)")
print("   └── individual_trips/     (250 grafici individuali)")
print("   └── SUMMARY_REPORT.txt    (report testuale)")
print()
print("2. /mnt/user-data/outputs/NETWORK_ANALYSIS_COMPLETE/")
print("   └── network_with_shared_arcs.png       (rete con sharing)")
print("   └── arc_sharing_distribution.png       (statistiche)")
print("   └── arc_sharing_statistics.xlsx        (dati completi)")
print("   └── individual_paths/                  (percorsi trip esempio)")
print("   └── REPORT_ARC_SHARING.txt             (report sharing)")
print()
print("="*80)
print("🖥️  PROSSIMO STEP: APP INTERATTIVA")
print("="*80)
print()
print("Per esplorare i risultati interattivamente, esegui:")
print()
print("    streamlit run app_interactive.py")
print()
print("L'app si aprirà nel browser e ti permetterà di:")
print("  - Visualizzare dashboard generale")
print("  - Analizzare singoli trip in dettaglio")
print("  - Confrontare più trip")
print("  - Esplorare statistiche avanzate")
print()
print("="*80)
print("📖 Per maggiori informazioni, leggi:")
print("    /mnt/user-data/outputs/README_ANALISI_250_TRIPS.md")
print("="*80)