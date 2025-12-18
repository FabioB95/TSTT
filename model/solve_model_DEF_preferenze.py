import json
import pandas as pd
from pyomo.environ import SolverFactory, value
from pyomo.opt import TerminationCondition

from model_DEF_preferenze import model

print("\n✅ Modello Pyomo caricata da model_DEF_preferenze.py")

# --- Caricamento dati trips per output dettagliato ---
try:
    with open("dati/trips_with_paths_temporal.json") as f:
        trips_data = json.load(f)["trips"]
    print("✅ Dati trips caricati per analisi risultati")
except FileNotFoundError:
    print("⚠️ 'dati/trips_with_paths_temporal.json' non trovato")
    trips_data = {}

# --- Risoluzione ---
print("\n🚀 Avvio risoluzione con Gurobi...")
solver = SolverFactory('gurobi')

solver.options['LogToConsole'] = 1
solver.options['MIPGap'] = 0.01
solver.options['TimeLimit'] = 3600

results = solver.solve(model, tee=True, load_solutions=True)

# --- Stato terminazione ---
if results.solver.termination_condition == TerminationCondition.optimal:
    print("\n✅ Soluzione OTTIMALE trovata!")
    print(f"Valore funzione obiettivo: {value(model.obj):,.2f}\n")

elif results.solver.termination_condition == TerminationCondition.infeasible:
    print("\n❌ Modello INFEASIBILE")
    model.write('model_infeasible_debug.lp', format='lp', io_options={'symbolic_solver_labels': True})
    solver.options['iisfind'] = 1
    solver.solve(model, tee=True)
    print("File model_infeasible_debug.lp generato per debug IIS")
    exit(1)

elif results.solver.termination_condition == TerminationCondition.unbounded:
    print("\n⚠️ Modello ILLIMITATO")
    exit(1)

elif results.solver.termination_condition == TerminationCondition.timeLimit:
    print("\n⏰ Timeout raggiunto, soluzione parziale")
    if results.solver.status == 'ok':
        print(f"Valore funzione obiettivo: {value(model.obj):,.2f}\n")
    else:
        print("Nessuna soluzione valida trovata")
        exit(1)

else:
    print(f"\n❓ Stato terminazione sconosciuto: {results.solver.termination_condition}")
    exit(1)

# --- Output dettagliato ---
VALUE_THRESHOLD = 1e-8

print("\n--- DEBUG primi valori sigma ---")
counter = 0
for (i,j,t) in model.A * model.T:
    if counter >= 10:
        break
    val = model.sigma[i,j,t].value
    print(f"sigma[{i},{j},{t}] = {val:.3f}" if val is not None else f"sigma[{i},{j},{t}] = N/A")
    counter += 1

print("\n🚗 Assegnazione y[c,p,t]:")
assignments = []
for (c,p,t) in model.CTP:
    val = model.y[c,p,t].value
    if val is not None and val > VALUE_THRESHOLD:
        trip = trips_data[c]
        path = trip.get("paths", [])[p] if p < len(trip.get("paths", [])) else {}
        arcs = [(a[0], a[1]) for a in path.get("arcs", [])]

        preferred_times = [int(pt) for pt in trip.get("departure_times", [])]
        real_departure_time = int(t)


# Cerca se il tempo reale coincide con una preferenza
        matched_preference = None
        for pt in preferred_times:
            if pt == real_departure_time:
                matched_preference = pt
                break

# Se non coincide, trova la preferenza più vicina (per calcolare il delay)
        if matched_preference is not None:
            delay = 0
        else:
            matched_preference = min(preferred_times, key=lambda x: abs(x - real_departure_time)) if preferred_times else None
            delay = real_departure_time - matched_preference if matched_preference is not None else 0

        kept_preference = (delay == 0)



        fftt_total = model.fftt_c[c]
        real_time = model.c_cost[c,p,t]
        inconvenience = real_time / fftt_total if fftt_total > 0 else 1.0

        print(f"Trip {c} - tempo {t}, path {p}, veicoli={val:.1f}, delay={delay}, inconvenience={inconvenience:.2f}, percorso={arcs}, kept_pref={kept_preference}")

        assignments.append({
            "trip": c,
            "departure_time": real_departure_time,
            "path_index": p,
            "vehicles": round(val, 2),
            "delay": int(delay),
            "real_departure_time": real_departure_time,
            "preferred_time": matched_preference,
            "all_preferences": preferred_times,
            "kept_preference": kept_preference,
            "inconvenience": round(inconvenience, 3)
        })


if not assignments:
    print("Nessun valore 'y' significativo trovato.")

print("\n--- Flussi x[i,j,t] ---")
flows = []
for (i,j,t) in model.A * model.T:
    val = model.x[i,j,t].value
    if val is not None and val > VALUE_THRESHOLD:
        print(f"Arco {i}->{j} tempo {t}: flusso={val:.1f}")
        flows.append({
            "arc": f"{i}->{j}",
            "time": t,
            "flow": round(val, 2)
        })

if not flows:
    print("Nessun valore 'x' significativo trovato.")

print("\n--- TTI sigma[i,j,t] ---")
tti_estimates = []
for (i,j,t) in model.A * model.T:
    val = model.sigma[i,j,t].value
    if val is not None and val > VALUE_THRESHOLD:
        print(f"Arco {i}->{j} tempo {t}: sigma={val:.3f}")
        tti_estimates.append({
            "arc": f"{i}->{j}",
            "time": t,
            "tti": round(val, 3)
        })

if not tti_estimates:
    print("Nessun valore 'sigma' significativo trovato.")

print("\n🎉 Processo completato!")


import pandas as pd

# Salvataggio y (assegnazioni)
if assignments:
    pd.DataFrame(assignments).to_csv("y_DEF_preferenze.csv", index=False)
    print("✅ File y_DEF_preferenze.csv salvato")
else:
    print("⚠️ Nessun dato 'y' significativo da salvare")

# Salvataggio x (flussi)
if flows:
    pd.DataFrame(flows).to_csv("x_DEF_preferenze.csv", index=False)
    print("✅ File x_DEF_preferenze.csv salvato")
else:
    print("⚠️ Nessun dato 'x' significativo da salvare")


# Salvataggio in formato SpreadsheetML (Excel .xml)
import xml.etree.ElementTree as ET

df = pd.DataFrame(assignments)


if not df.empty:
    root = ET.Element("Workbook", {
        "xmlns": "urn:schemas-microsoft-com:office:spreadsheet",
        "xmlns:o": "urn:schemas-microsoft-com:office:office",
        "xmlns:x": "urn:schemas-microsoft-com:office:excel",
        "xmlns:ss": "urn:schemas-microsoft-com:office:spreadsheet",
        "xmlns:html": "http://www.w3.org/TR/REC-html40"
    })

    worksheet = ET.SubElement(root, "Worksheet", {"ss:Name": "y_DEF_preferenze"})
    table = ET.SubElement(worksheet, "Table")

    # Intestazione
    header_row = ET.SubElement(table, "Row")
    for col in df.columns:
        cell = ET.SubElement(header_row, "Cell")
        data = ET.SubElement(cell, "Data", {"ss:Type": "String"})
        data.text = str(col)

    # Dati
    for _, row in df.iterrows():
        xml_row = ET.SubElement(table, "Row")
        for item in row:
            cell = ET.SubElement(xml_row, "Cell")
            data = ET.SubElement(cell, "Data", {"ss:Type": "String"})
            data.text = str(item)

    # Scrittura su file
    tree = ET.ElementTree(root)
    tree.write("y_DEF_preferenze.xml", encoding="utf-8", xml_declaration=True)
    print("✅ File y_DEF_preferenze.xml (Excel XML) salvato correttamente.")
else:
    print("⚠️ Nessun dato 'y' da salvare in formato Excel XML.")
