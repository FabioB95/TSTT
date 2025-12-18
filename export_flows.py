"""
Export Time-Specific Flow Data from ITER-FLOW Solution
This script reads your Pyomo model solution and exports arc flows for each time slot
Run this AFTER your solve_1.py completes
"""

import pandas as pd
import json
from pyomo.environ import value

def export_time_specific_flows(model, ARCS, TIME_SLOTS, output_file="arc_flows_by_time.json"):
    """
    Export arc flows for each time slot to JSON
    
    Parameters:
    -----------
    model : Pyomo model with solution loaded
    ARCS : List of (from, to) tuples
    TIME_SLOTS : List of time slot indices
    output_file : Output JSON filename
    """
    print("\n" + "="*60)
    print("EXPORTING TIME-SPECIFIC FLOW DATA")
    print("="*60)
    
    flows_by_time = {}
    
    for (i, j) in ARCS:
        arc_key = f"{i},{j}"
        flows_by_time[arc_key] = {}
        
        for t in TIME_SLOTS:
            try:
                flow = value(model.x[i, j, t], exception=False)
                if flow is not None:
                    flows_by_time[arc_key][str(t)] = float(flow)
                else:
                    flows_by_time[arc_key][str(t)] = 0.0
            except:
                flows_by_time[arc_key][str(t)] = 0.0
    
    # Save to JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(flows_by_time, f, indent=2)
    
    print(f"[OK] Exported time-specific flows to: {output_file}")
    print(f"     Arcs: {len(ARCS)}")
    print(f"     Time slots: {len(TIME_SLOTS)}")
    print(f"     Total data points: {len(ARCS) * len(TIME_SLOTS):,}")
    
    return flows_by_time


def export_to_excel_with_time(model, ARCS, TIME_SLOTS, FFTT, CAPACITY, output_file="arc_flows_detailed.xlsx"):
    """
    Export detailed arc flows to Excel with separate columns for key time slots
    """
    print("\n" + "="*60)
    print("EXPORTING DETAILED FLOW DATA TO EXCEL")
    print("="*60)
    
    arc_data = []
    
    # Time slots we care about (8AM, 12PM, 6PM)
    key_slots = [8, 24, 48]
    
    for (i, j) in ARCS:
        ff = FFTT.get((i, j), 0)
        mu = CAPACITY.get((i, j), 0)
        
        # Get flows at all time slots
        flows_all = []
        for t in TIME_SLOTS:
            try:
                flow = value(model.x[i, j, t], exception=False)
                flows_all.append(flow if flow is not None else 0.0)
            except:
                flows_all.append(0.0)
        
        # Get flows at key times
        flow_8am = flows_all[8] if len(flows_all) > 8 else 0.0
        flow_12pm = flows_all[24] if len(flows_all) > 24 else 0.0
        flow_6pm = flows_all[48] if len(flows_all) > 48 else 0.0
        
        # Compute statistics
        avg_flow = sum(flows_all) / len(flows_all) if flows_all else 0.0
        max_flow = max(flows_all) if flows_all else 0.0
        
        arc_data.append({
            'From': i,
            'To': j,
            'Free_Flow_Time_min': ff,
            'Capacity_15min': mu,
            'Ave_Flow': avg_flow,
            'Max_Flow': max_flow,
            'Flow_8AM_Slot8': flow_8am,
            'Flow_12PM_Slot24': flow_12pm,
            'Flow_6PM_Slot48': flow_6pm,
            'Util_8AM_%': (flow_8am / mu * 100) if mu > 0 else 0,
            'Util_12PM_%': (flow_12pm / mu * 100) if mu > 0 else 0,
            'Util_6PM_%': (flow_6pm / mu * 100) if mu > 0 else 0,
        })
    
    df = pd.DataFrame(arc_data)
    df.to_excel(output_file, index=False, sheet_name="Arc_Flows_By_Time")
    
    print(f"[OK] Exported detailed flow data to: {output_file}")
    print(f"     Columns include flows at 8AM, 12PM, and 6PM")
    print(f"     Use this file for time-specific visualizations!")
    
    return df


# Example usage - ADD THIS TO YOUR solve_1.py AFTER THE MODEL SOLVES:
"""
# After your model.solve() call succeeds, add:

# Export time-specific flows
flows_json = export_time_specific_flows(model, ARCS, TIME_SLOTS, "arc_flows_by_time.json")

# Export detailed Excel with time-specific columns
df_detailed = export_to_excel_with_time(model, ARCS, TIME_SLOTS, FFTT, CAPACITY, 
                                        "arc_flows_detailed.xlsx")

print("\n[OK] Time-specific flow data exported!")
print("    Use arc_flows_by_time.json for visualizations")
print("    Use arc_flows_detailed.xlsx for analysis")
"""

if __name__ == "__main__":
    print("="*60)
    print("Time-Specific Flow Export Utility")
    print("="*60)
    print("\nThis script should be imported and used within your solve_1.py")
    print("Add the following lines AFTER your model solves:")
    print("\n" + "="*60)
    print("from export_flows import export_time_specific_flows, export_to_excel_with_time")
    print("")
    print("# After model.solve():")
    print("export_time_specific_flows(model, ARCS, TIME_SLOTS, 'arc_flows_by_time.json')")
    print("export_to_excel_with_time(model, ARCS, TIME_SLOTS, FFTT, CAPACITY, 'arc_flows_detailed.xlsx')")
    print("="*60)