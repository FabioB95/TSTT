
from pyomo.environ import *
from model_test import model
import pandas as pd
import json

# --- Carica i dati dei trip per stampa path ---
with open("dati/trips_test.json") as f:
    trips_data = json.load(f)["trips"]


print("\n✅Dati trips caricati!")

# --- Risoluzione con Gurobi ---
solver = SolverFactory('gurobi')
results = solver.solve(model, tee=True)

# --- Valore ottimo ---
print(f"\n✅ Valore ottimo: {value(model.obj)}\n")

print("\n🔍 DEBUG: valori sigma per primi 10 archi-tempo")
counter = 0
for (i, j, t) in model.A * model.T:
    if counter >= 10:
        break
    print(f"sigma[{i},{j},{t}] = {model.sigma[i, j, t].value}")
    counter += 1


# --- Risultati: assegnazione y[c,p,t] con ritardo e inconvenience ---
print("🚗 Assegnazione y[c,p,t] con ritardo e inconvenience:")
assignments = []
for (c, p, t) in model.CTP:
    val = model.y[c, p, t].value
    if val and val > 0.1:
        trip = trips_data[c]
        path = trip["paths"][p]
        arcs = [(a[0], a[1]) for a in path["arcs"]]
        base_times = path["base_times"]

        # Ritardo: tempo reale - tempo ideale
        ideal_departure = min(path["possible_departure_times"])
        delay = t - ideal_departure

        # Inconvenience: tempo effettivo / tempo ideale
        
        fftt_total = model.fftt_c[c]
        real_time = model.c_cost [c, p, t]
        inconvenience = real_time / fftt_total if fftt_total > 0 else 1.0

        print(f"Trip {c} - partenza snapshot {t}, path {p}: {val:.1f}, delay: {delay}, inconvenience: {inconvenience:.2f}, path: {arcs}")

        assignments.append({
            "trip": c,
            "departure_time": t,
            "path_index": p,
            "vehicles": val,
            "delay": delay,
            "inconvenience": round(inconvenience, 3)
        })


# --- Risultati: flussi x[a,t] ---
print("\n🛣️ Flusso su archi x[a,t]:")
flows = []
for (i, j, t) in model.A * model.T:
    if model.x[i, j, t].value and model.x[i, j, t].value > 0.1:
        print(f"Arco {i}->{j} tempo {t}: {model.x[i, j, t].value:.1f}")
        flows.append({
            "arc": f"{i}->{j}",
            "time": t,
            "flow": model.x[i, j, t].value
        })

# --- Risultati: sigma (TTI stimato) ---
print("\n📉 TTI stimati sigma[i,j,t]:")
tti_estimates = []
for (i, j, t) in model.A * model.T:
    sigma_val = model.sigma[i, j, t].value
    if sigma_val is not None and sigma_val > 0:
        print(f"Arco {i}->{j}, tempo {t}: TTI = {model.sigma[i, j, t].value:.3f}")
        tti_estimates.append({
            "arc": f"{i}->{j}",
            "time": t,
            "tti": model.sigma[i, j, t].value
        })

# --- Salvataggio veicoli attivi per arco e tempo ---
with open("output_vehicle_on_arc.csv", "w") as f:
    f.write("arc,time,vehicles\n")
    for (i, j, t) in model.A * model.T:
        val = model.x[i, j, t].value
        if val and val > 0.01:
            f.write(f"{i}->{j},{t},{val:.2f}\n")


# --- Salvataggio CSV ---
pd.DataFrame(assignments).to_csv("output_y.csv", index=False)
pd.DataFrame(flows).to_csv("output_x.csv", index=False)
pd.DataFrame(tti_estimates).to_csv("output_sigma.csv", index=False)

print("\n📁 Risultati salvati in: output_y.csv, output_x.csv, output_sigma.csv")

with open("output_lambda.csv", "w") as f:
    f.write("arc,time,h,lambda\n")
    for (i,j,t,h) in model.ATH:
        if model.lmbda[i,j,t,h].value > 0.001:
            f.write(f"{i}->{j},{t},{h},{model.lmbda[i,j,t,h].value}\n")
