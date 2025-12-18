import os
import sys
import time
import math
import numpy as np
import pandas as pd
from collections import defaultdict
import logging
from pyomo.environ import *
from pyomo.opt import SolverFactory, TerminationCondition

logging.basicConfig(level=logging.INFO)
logging.getLogger("pyomo").setLevel(logging.WARNING)

OUT_XLS = "solution_250_MEDIUM.xlsx"
DEBUG_LOG = "debug_1.txt"

def safe_value(expr, default=0.0):
    try:
        val = value(expr, exception=False)
        return default if val is None else float(val)
    except:
        return default

print("\n" + "="*70)
print("🚀 ITERATIVE USER EQUILIBRIUM SOLVER")
print("   Implements 2-3 iterations with effective travel time updates")
print("="*70)

from model_MULTI import create_model, compute_effective_travel_times, bpr_latency_arc

log_file = open(DEBUG_LOG, "w", encoding="utf-8")
def log(msg):
    print(msg)
    log_file.write(msg + "\n")
    log_file.flush()

# ============================================================
# ITERATIVE PARAMETERS
# ============================================================
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "3"))
CONVERGENCE_THRESHOLD = float(os.getenv("CONV_THRESHOLD", "0.05"))  # 5% change

log(f"\n🔧 Iterative Parameters:")
log(f"   Max iterations: {MAX_ITERATIONS}")
log(f"   Convergence threshold: {CONVERGENCE_THRESHOLD*100:.1f}%")

# ============================================================
# SOLVER SETUP
# ============================================================
solver = SolverFactory("gurobi")
if not solver.available():
    raise RuntimeError("Gurobi not available")

solver.options.clear()
solver.options.update({
    "Method": 2,              # Barrier
    "Crossover": 0,           # No crossover
    "Presolve": 2,
    "Threads": 16,
    "TimeLimit": 72000,        
    "FeasibilityTol": 1e-3,
    "OptimalityTol": 1e-3,
    "BarConvTol": 1e-3,
    "NumericFocus": 2,
    "BarHomogeneous": 1,
})

# ============================================================
# ITERATIVE LOOP
# ============================================================
effective_times_history = []
objective_history = []
convergence_history = []

effective_travel_times = None  # Start with None (will use FF times)

# Variables to track final results
TSTT_final = 0.0
assign_rate_final = 0.0
I_bar_final = 0.0
total_slack_final = 0.0

for iteration in range(MAX_ITERATIONS):
    log("\n" + "="*70)
    log(f"ITERATION {iteration + 1}/{MAX_ITERATIONS}")
    log("="*70)
    
    # ============================================================
    # BUILD MODEL WITH CURRENT TRAVEL TIMES
    # ============================================================
    model, TRIPS_DATA, ARCS, TIME_SLOTS, FFTT, CAPACITY, Z, PATH_ARCS, gamma, total_demand, OBJ_SCALE, TRAVEL_TIMES = create_model(
        effective_travel_times=effective_travel_times,
        iteration=iteration
    )
    
    log(f"\n📊 Instance Statistics (Iteration {iteration + 1}):")
    log(f"   Total Demand: {total_demand:,.0f}")
    log(f"   CTP Options: {len(model.CTP):,}")
    log(f"   Arcs: {len(ARCS)}")
    log(f"   Time Slots: {len(TIME_SLOTS)}")
    
    # ============================================================
    # OPTIMIZE: MINIMIZE TSTT
    # ============================================================
    log(f"\n{'='*70}")
    log(f"OPTIMIZATION (Iteration {iteration + 1}): Minimize TSTT")
    log(f"{'='*70}")
    
    # Ensure correct objective is active
    if hasattr(model, 'obj_inconv'):
        model.obj_inconv.deactivate()
    model.obj_TSTT.activate()
    if hasattr(model, 'eps_cap'):
        model.eps_cap.deactivate()
    
    log("\n⏳ Solving...")
    t0 = time.time()
    results = solver.solve(model, tee=True, load_solutions=True)
    solve_time = time.time() - t0
    
    tc = results.solver.termination_condition
    log(f"\n{'='*70}")
    log(f"Termination: {tc}")
    log(f"Time: {solve_time:.1f}s ({solve_time/60:.1f} minutes)")
    
    # ============================================================
    # EVALUATE SOLUTION
    # ============================================================
    TSTT_scaled = safe_value(model.TSTT_total)
    TSTT = TSTT_scaled / OBJ_SCALE
    
    total_y = sum(safe_value(model.y[c,p,t]) for (c,p,t) in model.CTP)
    total_slack = sum(safe_value(model.r[c]) for c in model.C)
    assign_rate = 100 * total_y / total_demand
    
    def calc_inconvenience():
        total_inconv = 0.0
        total_flow = 0.0
        for (c, p, t) in model.CTP:
            y_val = safe_value(model.y[c, p, t])
            if y_val <= 1e-6:
                continue
            I_val = safe_value(model.I[c, p, t])
            total_inconv += I_val * y_val
            total_flow += y_val
        return (total_inconv / total_flow) if total_flow > 0 else 0.0
    
    I_bar = calc_inconvenience()
    
    log(f"\n📊 Iteration {iteration + 1} Results:")
    log(f"   TSTT (unscaled): {TSTT:,.2f}")
    log(f"   TSTT (scaled): {TSTT_scaled:,.2f}")
    log(f"   Assignment: {assign_rate:.1f}%")
    log(f"   Unmet: {total_slack:,.0f}")
    log(f"   Avg Inconvenience: {I_bar:.4f}")
    
    # Update final results (these will be from the last iteration)
    TSTT_final = TSTT
    assign_rate_final = assign_rate
    I_bar_final = I_bar
    total_slack_final = total_slack
    
    # Store objective for convergence check
    objective_history.append(TSTT)
    
    # ============================================================
    # COMPUTE NEW EFFECTIVE TRAVEL TIMES
    # ============================================================
    new_effective_times = compute_effective_travel_times(model, ARCS, TIME_SLOTS, FFTT, CAPACITY)
    effective_times_history.append(new_effective_times)
    
    # ============================================================
    # CHECK CONVERGENCE
    # ============================================================
    converged = False
    if iteration > 0:
        obj_change = abs(objective_history[-1] - objective_history[-2]) / objective_history[-2]
        convergence_history.append(obj_change)
        
        log(f"\n🔍 Convergence Check:")
        log(f"   Previous TSTT: {objective_history[-2]:,.2f}")
        log(f"   Current TSTT: {objective_history[-1]:,.2f}")
        log(f"   Change: {obj_change*100:.2f}%")
        
        if obj_change < CONVERGENCE_THRESHOLD:
            log(f"\n✅ CONVERGED after {iteration + 1} iterations!")
            log(f"   Change ({obj_change*100:.2f}%) < Threshold ({CONVERGENCE_THRESHOLD*100:.1f}%)")
            converged = True
        else:
            log(f"\n⚠️ Not converged yet. Continuing...")
    
    # Update for next iteration
    effective_travel_times = new_effective_times
    
    # Break if converged
    if converged:
        break

# ============================================================
# COMPUTE COMPREHENSIVE STATISTICS
# ============================================================
log("\n" + "="*70)
log("📊 COMPUTING COMPREHENSIVE STATISTICS")
log("="*70)

# Per-arc statistics
arc_stats = []
for (i, j) in ARCS:
    ff = FFTT[(i, j)]
    mu = CAPACITY[(i, j)]
    
    flows = []
    utils = []
    tt_increases = []
    
    for t in TIME_SLOTS:
        x_val = safe_value(model.x[i, j, t])
        flows.append(x_val)
        
        if mu > 0:
            util = (x_val / mu) * 100
            utils.append(util)
        
        # Compute travel time increase
        eff_tt = bpr_latency_arc(ff, mu, x_val)
        tt_increase = eff_tt - ff
        tt_increases.append(tt_increase)
    
    avg_flow = np.mean(flows)
    avg_util = np.mean(utils) if utils else 0.0
    max_flow = np.max(flows)
    max_util = np.max(utils) if utils else 0.0
    avg_tt_increase = np.mean(tt_increases)
    max_tt_increase = np.max(tt_increases)
    
    arc_stats.append({
        "From": i,
        "To": j,
        "Ave_Ave_Flow": round(avg_flow, 2),
        "Ave_Ave_Util": round(avg_util, 2),
        "Ave_Max_Flow": round(max_flow, 2),
        "Ave_Max_Util": round(max_util, 2),
        "Ave_AumentoTTArco": round(avg_tt_increase, 2),
        "Max_Ave_Flow": round(max_flow, 2),
        "Max_Ave_Util": round(max_util, 2),
        "Max_Max_Flow": round(max_flow, 2),
        "Max_Max_Util": round(max_util, 2),
        "Max_AumentoTTArco": round(max_tt_increase, 2),
    })

df_arc_stats = pd.DataFrame(arc_stats)

# Overall statistics
overall_stats = {
    "Ave_Ave_Flow": df_arc_stats["Ave_Ave_Flow"].mean(),
    "Ave_Ave_Util": df_arc_stats["Ave_Ave_Util"].mean(),
    "Ave_Max_Flow": df_arc_stats["Ave_Max_Flow"].mean(),
    "Ave_Max_Util": df_arc_stats["Ave_Max_Util"].mean(),
    "Ave_AumentoTTArco": df_arc_stats["Ave_AumentoTTArco"].mean(),
    "Max_Ave_Flow": df_arc_stats["Max_Ave_Flow"].max(),
    "Max_Ave_Util": df_arc_stats["Max_Ave_Util"].max(),
    "Max_Max_Flow": df_arc_stats["Max_Max_Flow"].max(),
    "Max_Max_Util": df_arc_stats["Max_Max_Util"].max(),
    "Max_AumentoTTArco": df_arc_stats["Max_AumentoTTArco"].max(),
    "Inconvenience_ave": I_bar_final
}

log(f"\n📊 Overall Statistics:")
for key, val in overall_stats.items():
    log(f"   {key}: {val:.2f}")

# ============================================================
# FINAL SUMMARY
# ============================================================
log("\n" + "="*70)
log("FINAL SUMMARY")
log("="*70)

log(f"\n🔁 Iterations completed: {len(objective_history)}")
log(f"\n📊 TSTT Evolution:")
for i, obj in enumerate(objective_history):
    log(f"   Iteration {i+1}: {obj:,.2f}")
    if i > 0:
        change = (obj - objective_history[i-1]) / objective_history[i-1] * 100
        log(f"      Change from previous: {change:+.2f}%")

if convergence_history:
    log(f"\n📉 Convergence History:")
    for i, conv in enumerate(convergence_history):
        log(f"   Iteration {i+2}: {conv*100:.2f}% change")

log(f"\n✅ FINAL METRICS:")
log(f"   TSTT: {TSTT_final:,.2f}")
log(f"   Inconvenience: {I_bar_final:.4f}")
log(f"   Assignment Rate: {assign_rate_final:.1f}%")
log(f"   Unmet Demand: {total_slack_final:,.0f}")

# ============================================================
# EXPORT RESULTS
# ============================================================
log(f"\n💾 Exporting results...")

# Assignments
assignments = []
for (c, p, t) in model.CTP:
    y_val = safe_value(model.y[c, p, t])
    if y_val <= 1e-4:
        continue
    path = PATH_ARCS.get((c, p), [])
    if not path:
        continue
    freeflow_tt = sum(FFTT[(i, j)] for (i, j) in path)
    effective_tt = sum(effective_travel_times[(i, j)] for (i, j) in path)
    tt_model = safe_value(model.TT[c, p, t])
    inconv_model = safe_value(model.I[c, p, t])
    assignments.append({
        "Trip_ID": c,
        "Path_ID": p,
        "Departure_Slot": t,
        "Vehicles_Assigned": y_val,
        "Demand": TRIPS_DATA[c]["demand"],
        "FreeFlow_Time_min": round(freeflow_tt, 2),
        "Effective_Time_min": round(effective_tt, 2),
        "TravelTime_PWL_min": round(tt_model, 2),
        "Inconvenience_PWL": round(inconv_model, 4),
    })

df_assignments = pd.DataFrame(assignments)

# Summary with comprehensive statistics
summary_data = {
    "Metric": [
        "Total_Demand", "CTP_Options", "Iterations",
        "Final_Assignment_%", "Final_TSTT", "Final_Inconvenience",
        "Ave_Ave_Flow", "Ave_Ave_Util", "Ave_Max_Flow", "Ave_Max_Util",
        "Ave_AumentoTTArco", "Max_Ave_Flow", "Max_Ave_Util",
        "Max_Max_Flow", "Max_Max_Util", "Max_AumentoTTArco", "Inconvenience_ave"
    ],
    "Value": [
        total_demand, len(model.CTP), len(objective_history),
        assign_rate_final, TSTT_final, I_bar_final,
        overall_stats["Ave_Ave_Flow"], overall_stats["Ave_Ave_Util"],
        overall_stats["Ave_Max_Flow"], overall_stats["Ave_Max_Util"],
        overall_stats["Ave_AumentoTTArco"], overall_stats["Max_Ave_Flow"],
        overall_stats["Max_Ave_Util"], overall_stats["Max_Max_Flow"],
        overall_stats["Max_Max_Util"], overall_stats["Max_AumentoTTArco"],
        overall_stats["Inconvenience_ave"]
    ]
}
df_summary = pd.DataFrame(summary_data)

# Convergence
conv_data = {
    "Iteration": list(range(1, len(objective_history) + 1)),
    "TSTT": objective_history,
    "Change_%": [0.0] + [c*100 for c in convergence_history]
}
df_convergence = pd.DataFrame(conv_data)

# Write to Excel
with pd.ExcelWriter(OUT_XLS, engine="openpyxl") as xl:
    df_summary.to_excel(xl, sheet_name="Summary", index=False)
    df_convergence.to_excel(xl, sheet_name="Convergence", index=False)
    df_arc_stats.to_excel(xl, sheet_name="Arc_Statistics", index=False)
    if not df_assignments.empty:
        df_assignments.to_excel(xl, sheet_name="Assignments", index=False)

log(f"\n💾 Results saved to: {OUT_XLS}")
log(f"   Sheets: Summary, Convergence, Arc_Statistics, Assignments")
log_file.close()

print(f"\n✅ COMPLETE - Final Assignment: {assign_rate_final:.1f}%")
print(f"   Converged in {len(objective_history)} iterations")
print(f"   Average Utilization: {overall_stats['Ave_Ave_Util']:.1f}%")
print(f"   Average TT Increase: {overall_stats['Ave_AumentoTTArco']:.1f} min")
print(f"   Average Inconvenience: {I_bar_final:.4f}")


# Import the export functions
from export_flows import export_time_specific_flows, export_to_excel_with_time

# After your model.solve() completes:
export_time_specific_flows(model, ARCS, TIME_SLOTS, "arc_flows_by_time.json")
export_to_excel_with_time(model, ARCS, TIME_SLOTS, FFTT, CAPACITY, "arc_flows_detailed.xlsx")