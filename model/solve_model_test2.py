import json
import pandas as pd
from pyomo.environ import SolverFactory, value
from pyomo.opt import TerminationCondition


from model_test2 import model

print("\n✅ Modello Pyomo caricato da model_test2.py!")

# --- Caricamento dati trips (necessario per l'output dettagliato) ---
try:
    with open("dati/trips_with_paths_temporal.json") as f:
        trips_data = json.load(f)["trips"]
    print("✅ Dati trips caricati per l'analisi dei risultati!")
except FileNotFoundError:
    print("⚠️ Attenzione: 'dati/trips_with_paths_temporal.json' non trovato. L'output dettagliato di 'y' potrebbe essere limitato.")
    trips_data = {} 

# --- Risoluzione con Gurobi ---
print("\n🚀 Avvio risoluzione del modello con Gurobi...")
solver = SolverFactory('gurobi')

# Impostazioni Gurobi:

solver.options['LogToConsole'] = 1 
solver.options['MIPGap'] = 0.01 
solver.options['TimeLimit'] = 3600 

results = solver.solve(model, tee=True, load_solutions=True) 

# --- Analisi dei risultati ---
print("\n--- Analisi Risultati Solutore ---")

# Gestione dello stato di terminazione del solutore
if results.solver.termination_condition == TerminationCondition.optimal:
    print("\n✅ Soluzione OTTIMALE trovata!")
    print(f"💰 Valore ottimo della funzione obiettivo: {value(model.obj):,.2f}\n")

elif results.solver.termination_condition == TerminationCondition.infeasible:
    print("\n❌ Il modello è INFEASIBILE. Non è stata trovata alcuna soluzione.")
    print("🔍 Tentativo di identificare un Irreducible Infeasible Subsystem (IIS)...")
    # Genera un file .lp del modello corrente per debug
    model.write('model_infeasible_debug.lp', format='lp', io_options={'symbolic_solver_labels': True})

    # Abilita la ricerca IIS in Gurobi
    solver.options['iisfind'] = 1
    solver.solve(model, tee=True)
    print("📄 File 'model_infeasible_debug.lp' generato (contiene il modello infeasible).")
    print("👉 Controlla l'output del solutore sopra per il 'Detailed IIS report'.")
    exit(1) # Esci se il modello è infeasible, dato che i risultati non sarebbero validi

elif results.solver.termination_condition == TerminationCondition.unbounded:
    print("\n⚠️ Il modello è ILLIMITATO. La funzione obiettivo può essere migliorata indefinitamente.")
    exit(1)

elif results.solver.termination_condition == TerminationCondition.timeLimit:
    print("\n⏰ Il solutore ha raggiunto il limite di tempo. Soluzione attuale potrebbe non essere ottimale.")
    if results.solver.status == 'ok':
        print(f"💰 Miglior valore obiettivo trovato: {value(model.obj):,.2f}\n")
    else:
        print("Il solutore ha raggiunto il limite di tempo senza trovare una soluzione valida.")
        exit(1)

else:
    print(f"\n❓ Il solutore ha terminato con uno stato sconosciuto: {results.solver.termination_condition}")
    print("Si prega di esaminare l'output del solutore per maggiori dettagli.")
    exit(1)

# --- Output Dettagliato dei Risultati (eseguito solo se il modello è fattibile) ---

# Soglia minima per la visualizzazione dei valori delle variabili
VALUE_THRESHOLD = 1e-8 

# --- DEBUG sigma: primi 10 valori (per verifica rapida) ---
print("\n🔍 DEBUG: Primi 10 valori di sigma[i,j,t] (se disponibili)")
counter = 0
for (i, j, t) in model.A * model.T:
    if counter >= 10:
        break
    try:
        val = model.sigma[i, j, t].value
        if val is not None:
            print(f"sigma[{i},{j},{t}] = {val:.3f}")
        else:
            print(f"sigma[{i},{j},{t}] = N/A (non assegnato)")
    except AttributeError: # Nel caso in cui il valore non sia disponibile
        print(f"sigma[{i},{j},{t}] = Errore lettura valore")
    counter += 1

# --- Assegnazione y[c,p,t] ---
print("\n🚗 Assegnazione y[c,p,t] (Veicoli assegnati a Trip/Percorso/Tempo):")
assignments = []
for (c, p, t) in model.CTP:
    val = model.y[c, p, t].value
    if val is not None and val > VALUE_THRESHOLD: # Filtra i valori molto piccoli
        trip = trips_data[c] 
        path = trip.get("paths", [])[p] if p < len(trip.get("paths", [])) else {}
        arcs = [(a[0], a[1]) for a in path.get("arcs", [])]
        base_times = path.get("base_times", [])

        # Calcolo ritardo
        ideal_departure = min(path.get("possible_departure_times", [t])) 
        delay = t - ideal_departure

        # Calcolo inconvenience
        fftt_total = model.fftt_c[c]
        real_time = model.c_cost[c, p, t]
        inconvenience = real_time / fftt_total if fftt_total > 0 else 1.0

        print(f"Trip {c} - snapshot {t}, path {p}, veicoli={val:.1f}, ritardo={delay}, inconvenienza={inconvenience:.2f}, percorso={arcs}")

        assignments.append({
            "trip": c,
            "departure_time": t,
            "path_index": p,
            "vehicles": round(val, 2),
            "delay": int(delay),
            "inconvenience": round(inconvenience, 3)
        })

if not assignments:
    print("Nessun valore 'y' significativo (> {}) trovato.".format(VALUE_THRESHOLD))


# --- Flussi x[i,j,t] ---
print("\n🛣️ Flussi su archi (x[i,j,t]):")
flows = []
for (i, j, t) in model.A * model.T:
    val = model.x[i, j, t].value
    if val is not None and val > VALUE_THRESHOLD: # Filtra i valori molto piccoli
        print(f"Arco {i}->{j} al tempo {t}: Flusso={val:.1f}")
        flows.append({
            "arc": f"{i}->{j}",
            "time": t,
            "flow": round(val, 2)
        })

if not flows:
    print("Nessun valore 'x' significativo (> {}) trovato.".format(VALUE_THRESHOLD))


# --- TTI sigma[i,j,t] ---
print("\n📉 TTI stimato per archi (sigma[i,j,t]):")
tti_estimates = []
for (i, j, t) in model.A * model.T:
    val = model.sigma[i, j, t].value
    if val is not None and val > VALUE_THRESHOLD: # Filtra i valori molto piccoli
        print(f"Arco {i}->{j} al tempo {t}: Sigma={val:.3f}")
        tti_estimates.append({
            "arc": f"{i}->{j}",
            "time": t,
            "tti": round(val, 3)
        })

if not tti_estimates:
    print("Nessun valore 'sigma' significativo (> {}) trovato.".format(VALUE_THRESHOLD))


# --- Lambda[i,j,t,h] ---
print("\n🔬 Lambda significativi (lmbda[i,j,t,h]):")
lambda_values = []
for (i, j, t, h) in model.ATH:
    val = model.lmbda[i, j, t, h].value
    if val is not None and val > VALUE_THRESHOLD: 
        lambda_values.append({
            "arc": f"{i}->{j}",
            "time": t,
            "segment": h,
            "lambda": round(val, 5)
        })

if not lambda_values:
    print("Nessun valore 'lambda' significativo (> {}) trovato.".format(VALUE_THRESHOLD))


# --- Salvataggio risultati CSV ---
print("\n📁 Salvataggio risultati in file CSV...")

if assignments:
    pd.DataFrame(assignments).to_csv("output_y_test2.csv", index=False)
    print("  • output_y_test2.csv")
else:
    print("  • Nessun dato 'y' da salvare.")

if flows:
    pd.DataFrame(flows).to_csv("output_x_test2.csv", index=False)
    print("  • output_x_test2.csv")
else:
    print("  • Nessun dato 'x' da salvare.")

if tti_estimates:
    pd.DataFrame(tti_estimates).to_csv("output_sigma_test2.csv", index=False)
    print("  • output_sigma_test2.csv")
else:
    print("  • Nessun dato 'sigma' da salvare.")

if lambda_values:
    pd.DataFrame(lambda_values).to_csv("output_lambda_test2.csv", index=False)
    print("  • output_lambda_test2.csv")
else:
    print("  • Nessun dato 'lambda' da salvare.")

# Salvataggio anche CSV semplice per veicoli su archi
if flows:
    with open("output_vehicle_on_arc_test2.csv", "w") as f:
        f.write("arc,time,vehicles\n")
        for row in flows:
            f.write(f"{row['arc']},{row['time']},{row['flow']:.2f}\n")
    print("  • output_vehicle_on_arc_test2.csv")
else:
    print("  • Nessun dato sui flussi da salvare in 'output_vehicle_on_arc_test2.csv'.")

print("\n🎉 Processo completato!")