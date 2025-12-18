from pyomo.environ import *
from model_DEF import model
import pandas as pd
import json

# --- Carica i dati dei trip per stampa path ---
with open("dati/trips_with_paths_temporal.json") as f:
    trips_data = json.load(f)["trips"]

print("\n✅ Dati trips caricati!")

# --- Risoluzione con Gurobi ---
solver = SolverFactory('gurobi')

results = solver.solve(model, tee=True)

# --- Valore ottimo ---
print(f"\n✅ Valore ottimo: {value(model.obj)}\n")

# --- Risultati: assegnazione y[c,p,t] ---
print("🚗 Assegnazione y[c,p,t]:")
assignments = []
for (c, p, t) in model.CTP:
    val = model.y[c, p, t].value
    if val and val > 0.1:
        trip = trips_data[c]
        path = trip["paths"][p]
        arcs = [(a[0], a[1]) for a in path["arcs"]]
        base_times = path["base_times"]

        ideal_departure = min(path["possible_departure_times"])
        delay = t - ideal_departure
        fftt_total = sum(base_times)
        inconvenience = fftt_total + delay  # Placeholder: da migliorare

        print(f"Trip {c} - partenza {t}, path {p}: {val:.1f}, delay: {delay}, path: {arcs}")

        assignments.append({
            "trip": c,
            "departure_time": t,
            "path_index": p,
            "vehicles": val,
            "inconvenience": inconvenience
        })

# --- Risultati: flussi x[a,t] ---
print("\n🛣️ Flusso su archi x[a,t]:")
flows = []
for (i, j, t) in model.A * model.T:
    val = model.x[i, j, t].value
    if val and val > 0.1:
        print(f"Arco {i}->{j}, tempo {t}: {val:.2f}")
        flows.append({
            "arc": f"{i}->{j}",
            "time": t,
            "flow": val
        })

# --- Risultati: eta[i,j,t] ---
print("\n📉 ETA stimati eta[i,j,t]:")
eta_vals = []
for (i, j, t) in model.A * model.T:
    val = model.eta[i, j, t].value
    if val and val > 0.001:
        print(f"ETA {i}->{j}, t={t}: {val:.4f}")
        eta_vals.append({
            "arc": f"{i}->{j}",
            "time": t,
            "eta": val
        })

# --- Risultati: lambda[i,j,t,h] ---
print("\n📊 Lambda:")
lambda_vals = []
for (i, j, t, h) in model.ATH:
    val = model.lmbda[i, j, t, h].value
    if val and val > 0.001:
        lambda_vals.append({
            "arc": f"{i}->{j}",
            "time": t,
            "h": h,
            "lambda": val
        })

# --- Esportazione CSV ---
pd.DataFrame(assignments).to_csv("output_y_DEF.csv", index=False)
pd.DataFrame(flows).to_csv("output_x_DEF.csv", index=False)
pd.DataFrame(eta_vals).to_csv("output_eta_DEF.csv", index=False)
pd.DataFrame(lambda_vals).to_csv("output_lambda_DEF.csv", index=False)

print("\n📁 Risultati salvati in: output_y_DEF.csv, output_x_DEF.csv, output_eta_DEF.csv, output_lambda_DEF.csv")
