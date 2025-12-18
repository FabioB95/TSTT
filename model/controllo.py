
import random
from pyomo.environ import SolverFactory, value
import matplotlib.pyplot as plt
from model_test import model
import numpy as np

random.seed(0)
# === Risolvo il modello con Gurobi (stessa configurazione di solve_model_test.py) ===
solver = SolverFactory('gurobi')
results = solver.solve(model, tee=False)

# Tolleranza per confronti floating‐point
TOL = 1e-6

# === 1. Controllo capacità sugli archi ===

print("\n=== 1. Controllo capacità sugli archi ===")
violazioni_capacita = False

# Per ogni arco (i,j) e ogni snapshot t
for (i, j) in model.A:
    cap = value(model.mu[i,j]) * 4 
    for t in model.T:
        x_val = value(model.x[i,j,t])
        if x_val is None:
            x_val = 0.0
        if x_val - cap > TOL:
            violazioni_capacita = True
            print(f"⛔ Violazione capacità: arco {i}->{j}, t={t}, x={x_val:.4f} > cap={cap:.4f}")
print("✔︎ Nessuna violazione di capacità." if not violazioni_capacita else "")

# === 2. Controllo sigma (TTI) su un campione casuale di (i,j,t) ===
#     Verifico che model.sigma[i,j,t] == 1 + sum_h [ (tti_h - tti_h_prev)/(b - b_prev) * lambda[i,j,t,h] ] ===

print("\n=== 2. Controllo sigma (Travel Time Index) su un campione casuale ===")
all_ijt = list({ (i,j,t) for (i,j,t,h) in model.ATH })
# Seleziono 10 tuple random
campione = random.sample(all_ijt, min(10, len(all_ijt)))
errori_sigma = False

for (i, j, t) in campione:
    # Valore sigma del modello
    sigma_model = value(model.sigma[i,j,t])
    if sigma_model is None:
        sigma_model = 0.0

    # Calcolo la somma dei contributi lambda
    sommatoria = 0.0
    for h in model.H[i,j]:
        lambda_val = value(model.lmbda[i,j,t,h])
        if lambda_val is None:
            lambda_val = 0.0
        # parametri della linearizzazione
        tti_h = value(model.tti_h[i,j,t,h])
        tti_h_prev = value(model.tti_h_prev[i,j,t,h])
        b = value(model.b[i,j,t,h])
        b_prev = value(model.b_prev[i,j,t,h])
        # contributo per questo h
        if abs(b - b_prev) < TOL:
            continue
        coeff = (tti_h - tti_h_prev) / (b - b_prev)
        sommatoria += coeff * lambda_val

    sigma_calc = 1.0 + sommatoria

    # Verifico la corrispondenza entro tolleranza
    if abs(sigma_model - sigma_calc) > 1e-4:
        errori_sigma = True
        print(f"⛔ Sigma mismatch su arco {i}->{j}, t={t}:")
        print(f"    sigma_model = {sigma_model:.6f}, sigma_calc = {sigma_calc:.6f}")

    else:
        print(f"✔︎ Sigma OK su arco {i}->{j}, t={t}: valore ≈ {sigma_model:.6f}")

print("✔︎ Tutti i campioni sigma sono corretti." if not errori_sigma else "")

# === 3. Controllo lambda: verificare che 
#     sum_h lambda[i,j,t,h] == x[i,j,t] per ogni (i,j,t) nel campione selezionato prima===

print("\n=== 3. Controllo somma lambda = x su un campione casuale di (i,j,t) ===")
errori_lambda = False

# Campione di tuple (i,j,t) da controllare
for (i,j,t) in campione:
    x_val = value(model.x[i,j,t]) or 0.0
    somm_lambda = 0.0
    for h in model.H[i,j]:
        somm_lambda += value(model.lmbda[i,j,t,h]) or 0.0

    if abs(x_val - somm_lambda) > 1e-4:
        errori_lambda = True
        print(f"⛔ Lambda mismatch su arco {i}->{j}, t={t}: sum(lambda) = {somm_lambda:.6f}, x = {x_val:.6f}")
    else:
        print(f"✔︎ Lambda OK su arco {i}->{j}, t={t}: sum(lambda) ≈ {somm_lambda:.6f} = x")

print("✔︎ Tutti i campioni lambda sommano a x correttamente." if not errori_lambda else "")

# === Fine controllo ===
print("\n=== Controlli terminati ===")


