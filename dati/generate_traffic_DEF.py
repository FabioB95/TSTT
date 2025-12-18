import json
import os
import numpy as np
import pandas as pd

print("\n" + "="*60)
print("🚀 GENERAZIONE TRAFFICO ESISTENTE (Z) - DEBUG MODE")
print("="*60)

# === Parametri ===
M = 1.5  # 0.5 = low, 1.0 = normal, 1.5 = high
PROFILE_FILE = "arc_traffic_high.json"
ARCS_FILE = "arcs_bidirectional.json"
OUTPUT_FILE = "traffic_DEF_H.json"
EXPECTED_SNAPSHOTS = 108

# === Caricamento ===
print("\n🔍 Caricamento file...")
assert os.path.exists(PROFILE_FILE), f"❌ File non trovato: {PROFILE_FILE}"
assert os.path.exists(ARCS_FILE), f"❌ File non trovato: {ARCS_FILE}"

with open(PROFILE_FILE, "r") as f:
    arc_traffic = json.load(f)
print(f"✅ Profilo traffico caricato: {len(arc_traffic)} archi")

with open(ARCS_FILE, "r") as f:
    arcs_data = json.load(f)["edges"]
print(f"✅ Archi caricati: {len(arcs_data)} archi")

# === Capacità per arco ===
capacity_dict = {}
for a in arcs_data:
    i, j = str(a["from_node"]), str(a["to_node"])
    cap = float(a["capacity"])
    capacity_dict[(i, j)] = cap
print(f"✅ Mappa capacità creata: {len(capacity_dict)} archi")

# === Verifica snapshot ===
print("\n🕒 Analisi snapshot...")
first_key = list(arc_traffic.keys())[0]
times = sorted(int(t) for t in arc_traffic[first_key].keys())
print(f"   Primo arco ha {len(times)} snapshot: {times[:5]}...{times[-5:]}")
assert len(times) == EXPECTED_SNAPSHOTS, f"❌ Attesi {EXPECTED_SNAPSHOTS}, trovati {len(times)}"
print(f"✅ Snapshot OK: {EXPECTED_SNAPSHOTS} presenti")

# === Generazione Z ===
print("\n🧮 Calcolo flusso esogeno Z...")
traffic_DEF = {}
total_flows = []
zero_flows = 0
arcs_not_found = []

for arc_key, profile in arc_traffic.items():
    i, j = arc_key.split(",")
    i, j = i.strip(), j.strip()
    cap = capacity_dict.get((i, j))

    if cap is None:
        arcs_not_found.append(arc_key)
        continue

    scaled_cap = cap / 4.0  # veicoli/15min
    traffic_DEF[arc_key] = {}

    for t in range(EXPECTED_SNAPSHOTS):
        factor = profile.get(str(t), 0.0)
        flow = round(M * factor * scaled_cap, 2)
        flow = max(0.0, flow)
        traffic_DEF[arc_key][str(t)] = flow
        total_flows.append(flow)
        if flow < 1e-6:
            zero_flows += 1

print(f"✅ Flussi generati per {len(traffic_DEF)} archi")
print(f"📊 Statistiche flussi:")
print(f"   - Totale valori: {len(total_flows):,}")
print(f"   - Media: {np.mean(total_flows):.2f}")
print(f"   - Max: {np.max(total_flows):.2f}")
print(f"   - Min (non-zero): {min(f for f in total_flows if f > 0):.2f}")
print(f"   - Zeri: {zero_flows:,} ({100*zero_flows/len(total_flows):.1f}%)")

# === Salvataggio ===
print(f"\n💾 Salvataggio in {OUTPUT_FILE}...")
with open(OUTPUT_FILE, "w") as f:
    json.dump(traffic_DEF, f, indent=2)
print(f"✅ Salvataggio completato")

# === Verifica finale ===
with open(OUTPUT_FILE, "r") as f:
    saved = json.load(f)
print(f"🔍 Verifica file salvato: {len(saved)} archi, {len(saved[list(saved.keys())[0]])} snapshot")

if arcs_not_found:
    print(f"⚠️ Archi non trovati: {arcs_not_found[:5]} (totale: {len(arcs_not_found)})")
else:
    print("✅ Tutti gli archi hanno capacità definita")

print("\n🎉 GENERAZIONE TRAFFICO COMPLETATA\n")