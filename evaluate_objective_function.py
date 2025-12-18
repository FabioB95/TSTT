import pandas as pd
import numpy as np
from pyomo.environ import *
from model_DEF_Gamma_filter import model, TRIPS_DATA, ARCS, TIME, FFTT, CAPACITY, ARC_DUR, CAP_scaled

# --- 1. Manually assign values to variables (you can modify these) ---
def assign_values(model):
    print("🔧 Assigning manual values to x and eta...")
    for (i, j) in ARCS:
        for t in TIME:
            # assign 10 vehicles to each arc at each time
            model.x[i, j, t] = 5000000  
            
            # assign travel time as free-flow time (no congestion)
            fftt = FFTT[(i, j)]
            model.eta[i, j, t] = fftt

    print("✅ Values assigned.")
    return model

# --- 2. Compute objective function manually ---
def compute_objective(model):
    print("🧮 Computing objective function manually...")
    eps = 1e-4
    obj_value = 0

    for (i, j) in model.A:
        for t in model.T:
            x_val = value(model.x[i, j, t], exception=False) or 0.0
            eta_val = value(model.eta[i, j, t], exception=False) or 0.0
            obj_value += eta_val + eps * x_val

    print(f"🎯 Objective function value: {obj_value}")
    return obj_value

# --- 3. Optional: Export variable values to Excel for inspection ---
def export_assigned_values(model, filename="manual_values.xlsx"):
    print(f"📂 Exporting variable values to '{filename}'...")
    rows = []

    for (i, j) in model.A:
        for t in model.T:
            x_val = value(model.x[i, j, t], exception=False) or 0.0
            eta_val = value(model.eta[i, j, t], exception=False) or 0.0
            rows.append({
                "From": i,
                "To": j,
                "Time": t,
                "x[i,j,t]": x_val,
                "eta[i,j,t]": eta_val
            })

    df = pd.DataFrame(rows)
    df.to_excel(filename, index=False)
    print(f"✅ Exported variable values to '{filename}'")

# --- MAIN ---
if __name__ == "__main__":
    print("🏗️  Starting manual objective evaluation script")

    # Step 1: Assign values to variables
    model = assign_values(model)

    # Step 2: Compute objective
    obj_value = compute_objective(model)

    # Step 3: (Optional) Export assigned values
    export_assigned_values(model)

    print("✅ Done.")