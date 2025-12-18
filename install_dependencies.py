"""
INSTALLAZIONE DIPENDENZE - Helper Script
Installa le librerie necessarie per l'app interattiva
"""

import subprocess
import sys

print("="*80)
print("📦 INSTALLAZIONE DIPENDENZE")
print("="*80)

libraries = [
    "streamlit",
    "pandas",
    "matplotlib",
    "numpy",
    "seaborn",
    "networkx",
    "openpyxl"
]

print("\n📋 Librerie da installare:")
for lib in libraries:
    print(f"   • {lib}")

print("\n⏳ Inizio installazione...")
print("-" * 80)

failed = []
for lib in libraries:
    print(f"\n📦 Installando {lib}...", end=" ")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", lib],
            capture_output=True,
            text=True,
            check=True
        )
        print("✓ OK")
    except subprocess.CalledProcessError as e:
        print("✗ FALLITO")
        failed.append(lib)
        print(f"   Errore: {e.stderr[:200]}")

print("\n" + "="*80)
if not failed:
    print("✅ INSTALLAZIONE COMPLETATA CON SUCCESSO!")
    print("="*80)
    print("\n🚀 Ora puoi eseguire:")
    print("\n   streamlit run app_interactive.py")
    print("\nL'app si aprirà automaticamente nel browser.")
else:
    print(f"⚠️  INSTALLAZIONE PARZIALE - {len(failed)} librerie fallite")
    print("="*80)
    print("\n❌ Librerie non installate:")
    for lib in failed:
        print(f"   • {lib}")
    print("\n💡 Prova a installarle manualmente:")
    print(f"\n   pip install {' '.join(failed)}")

print("="*80)