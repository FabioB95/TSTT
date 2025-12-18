from pyomo.environ import *
from model_test_pref import model
import pandas as pd
import json

# --- Carica i dati dei trip per stampa path e preferenze ---
with open("dati/trips_test.json") as f:
    trips_data = json.load(f)["trips"]

# --- Risoluzione con Gurobi ---
solver = SolverFactory('gurobi')
results = solver.solve(model, tee=True)

# --- Valore ottimo ---
print(f"\n✅ Valore ottimo: {value(model.obj)}\n")

# --- Risultati: assegnazione y[c,p,t] con dettaglio preferenza ===
print("🚗 Assegnazione y[c,p,t] con ritardo, inconvenience e rispetto preferenza:")
assignments = []
pref_kept_count = 0
pref_changed_count = 0

for (c, p, t) in model.CTP:
    y_val = model.y[c, p, t].value or 0.0
    if y_val > 0.1:
        trip = trips_data[c]
        path = trip["paths"][p]
        arcs = [(a[0], a[1]) for a in path["arcs"]]
        base_times = path["base_times"]

        # Tempo preferito per questo trip
        pref_t = trip["departure_times"][0]

        # Ritardo: differenza rispetto al più piccolo possibile nel path (resta come nel modello base)
        ideal_departure = min(path["possible_departure_times"])
        delay = t - ideal_departure

        # Inconvenience: tempo effettivo / tempo ideale
        fftt_total = model.fftt_c[c]
        real_time = model.c_cost[c, p, t]
        inconvenience = real_time / fftt_total if fftt_total > 0 else 1.0

        # Verifica se è nel tempo preferito
        kept = (t == pref_t)
        if kept:
            pref_kept_count += y_val
        else:
            pref_changed_count += y_val

        print(
            f"Trip {c} - path {p}, τ={t}, veicoli={y_val:.1f}, delay={delay}, "
            f"inconvenience={inconvenience:.2f}, preferito={'Sì' if kept else 'No'}, path={arcs}"
        )

        assignments.append({
            "trip": c,
            "path_index": p,
            "departure_time": t,
            "vehicles":round(y_val, 2),
            "delay": delay,
            "inconvenience": round(inconvenience, 3),
            "preferred_time": pref_t,
            "kept_preference": kept
        })

print(f"\n📊 Veicoli che hanno mantenuto preferenza: {pref_kept_count:.1f}")
print(f"📊 Veicoli che hanno cambiato preferenza: {pref_changed_count:.1f}")

# --- Risultati: flussi x[a,t] ---
print("\n🛣️ Flusso su archi x[a,t]:")
flows = []
for (i, j, t) in model.A * model.T:
    x_val = model.x[i, j, t].value or 0.0
    if x_val > 0.1:
        print(f"Arco {i}->{j} tempo {t}: {x_val:.1f}")
        flows.append({
            "arc": f"{i}->{j}",
            "time": t,
            "flow": x_val
        })

# --- Risultati: sigma (TTI stimato) ---
print("\n📉 TTI stimati sigma[i,j,t]:")
tti_estimates = []
for (i, j, t) in model.A * model.T:
    sigma_val = model.sigma[i, j, t].value or 0.0
    if sigma_val > 0:
        print(f"Arco {i}->{j}, tempo {t}: TTI = {sigma_val:.3f}")
        tti_estimates.append({
            "arc": f"{i}->{j}",
            "time": t,
            "tti": sigma_val
        })

# --- Salvataggio risultati su CSV ---
pd.DataFrame(assignments).to_csv("output_y_pref.csv", index=False)
pd.DataFrame(flows).to_csv("output_x_pref.csv", index=False)
pd.DataFrame(tti_estimates).to_csv("output_sigma_pref.csv", index=False)

print("\n📁 Risultati salvati in:")
print("  • output_y_pref.csv (assegnazioni con preferenze)")
print("  • output_x_pref.csv (flussi x[a,t])")
print("  • output_sigma_pref.csv (sigma stimati)")
