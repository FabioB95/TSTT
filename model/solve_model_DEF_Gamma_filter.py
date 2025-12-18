from pyomo.environ import *
from model_DEF_Gamma_filter import model, TRIPS_DATA, gamma
import pandas as pd

# === Solving ===
print("\n🔧 Avvio risoluzione...")
solver = SolverFactory("gurobi")
if not solver.available():
    print("❌ Gurobi non disponibile, provo con GLPK...")
    solver = SolverFactory("glpk")

results = solver.solve(model, tee=True)

# Check solve status
if results.solver.termination_condition == TerminationCondition.optimal:
    print("✅ Soluzione ottima trovata!")
    
    # === Output Results ===
    assignments = []
    for (c, p, t) in model.CTP:
        val = model.y[c, p, t].value
        if val and val > 1e-5:
            path = TRIPS_DATA[c]["paths"][p]
            assignments.append({
                "trip": c,
                "departure_time": t,
                "path_index": p,
                "vehicles": val,
                "path_length": len(path["arcs"]),
                "travel_time": path["time"]
            })

    flows = []
    for (i, j) in model.A:
        for t in model.T:
            val = model.x[i, j, t].value
            if val and val > 0.0001:
                flows.append({
                    "arc": f"{i}->{j}",
                    "time": t,
                    "flow": val
                })

    # Save results
    pd.DataFrame(assignments).to_csv("output_y_Gamma_fixed_1000.csv", index=False)
    pd.DataFrame(flows).to_csv("output_x_Gamma_fixed_1000.csv", index=False)

    print(f"\n📁 Risultati salvati in: output_y_Gamma_fixed.csv, output_x_Gamma_fixed.csv")
    print(f"🚗 Assegnazioni attive: {len(assignments)}")
    print(f"🚗 Flussi attivi: {len(flows)}")
    
