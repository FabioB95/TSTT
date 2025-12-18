import json
import math
import os
import pathlib
from collections import defaultdict

import numpy as np
import pandas as pd
from pyomo.environ import (ConcreteModel, Set, Param, Var, NonNegativeReals, Objective,
                           Constraint, Expression, minimize, value)

def _num(x):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return 0.0
    s = str(x).strip().replace(" ", "")
    if s.count(",") == 1 and s.count(".") == 0:
        s = s.replace(",", ".")
    elif s.count(".") > 1 and "," not in s:
        s = s.replace(".", "")
    elif s.count(",") > 1 and "." not in s:
        s = s.replace(",", "")
    return float(s)

def _pfloat(x):
    if isinstance(x, (int, float, np.floating)):
        return float(x)
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return float('nan')
    s = str(x).strip().replace(",", ".")
    try:
        return float(s)
    except:
        return float('nan')

def _parse_path_string(pstr):
    arcs = []
    if pstr is None or (isinstance(pstr, float) and np.isnan(pstr)):
        return arcs
    for tok in str(pstr).split(","):
        tok = tok.strip()
        if not tok or "_" not in tok:
            continue
        a, b = tok.split("_")
        arcs.append((str(a), str(b)))
    return arcs

def _parse_int_list(csv_like):
    if csv_like is None or (isinstance(csv_like, float) and np.isnan(csv_like)):
        return []
    out = []
    for s in str(csv_like).split(","):
        s = s.strip()
        if not s:
            continue
        try:
            out.append(int(float(s)))
        except:
            pass
    return out

def bpr_latency_arc(ff, mu, x):
    """BPR latency function: returns EFFECTIVE travel time on an arc"""
    if mu <= 0:
        return ff
    return ff * (1.0 + 0.15 * (x / mu) ** 4)

def bpr_sigma_arc(ff, mu, x):
    """Beckmann potential integral"""
    if mu <= 0:
        return ff * x
    return ff * (x + 0.15 * (x ** 5) / (5.0 * (mu ** 4)))

def create_model(effective_travel_times=None, iteration=0):
    """
    Create the optimization model.
    
    Parameters:
    -----------
    effective_travel_times : dict, optional
        Dictionary mapping (i,j) -> effective travel time (in minutes)
        If None, uses free-flow times
    iteration : int
        Current iteration number (0 = first run with FF times)
    """
    print("\n" + "=" * 60)
    print(f"🚀 BUILDING MODEL - ITERATION {iteration}")
    if iteration == 0:
        print("   Using FREE-FLOW travel times")
    else:
        print("   Using EFFECTIVE travel times from previous iteration")
    print("=" * 60)

    # ============================================================
    # MODIFIED PARAMETERS
    # ============================================================
    U_TTI = float(os.getenv("U_TTI", "4.0"))  # Changed from 6.5 to 4.0
    GAMMA = float(os.getenv("GAMMA", "0.25"))  # Changed from 0.30 to 0.25
    EPSILON = float(os.getenv("EPSILON", "0.20"))
    DELTA_MIN = int(os.getenv("DELTA_MIN", "15"))
    TIME_SLOTS = list(range(108))
    
    u_max_raw = ((U_TTI - 1.0) / 0.15) ** 0.25
    u_max = u_max_raw * 1.10
    print(f"🔧 U_TTI={U_TTI}, u_max={u_max:.3f}, GAMMA={GAMMA}")
    
    Z_SCALE = float(os.getenv("Z_SCALE", "0.6"))
    if Z_SCALE != 1.0:
        print(f"🔧 Background traffic scaled by {Z_SCALE}")

    # Load Dataset
    xls_path = os.getenv("XLS_PATH", "./INPUT_DATASETS/MEDIUM/OTT/dataset_medium_traffic_250.xlsx")
    if not pathlib.Path(xls_path).exists():
        raise FileNotFoundError(f"❌ Excel file '{xls_path}' not found")
    df_nodes = pd.read_excel(xls_path, sheet_name="nodes")
    df_arcs = pd.read_excel(xls_path, sheet_name="arcs")
    df_trips = pd.read_excel(xls_path, sheet_name="trips")
    print(f"📂 Dataset: {xls_path}")

    # Process Arcs
    ARCS = [(str(r["from_node"]), str(r["to_node"])) for _, r in df_arcs.iterrows()]
    NODES = df_nodes["ID"].astype(str).tolist()
    CAPACITY_HR = {(str(r["from_node"]), str(r["to_node"])): _num(r["capacity"]) for _, r in df_arcs.iterrows()}
    CAPACITY = {(i, j): CAPACITY_HR[(i, j)] / 4.0 for (i, j) in ARCS}
    FFTT = {(str(r["from_node"]), str(r["to_node"])): _num(r["fftt"]) for _, r in df_arcs.iterrows()}
    
    # ============================================================
    # KEY CHANGE: Use effective travel times if provided
    # ============================================================
    if effective_travel_times is None:
        # First iteration: use free-flow times
        TRAVEL_TIMES = FFTT.copy()
        print("   📏 Using FREE-FLOW travel times for path selection")
    else:
        # Subsequent iterations: use effective times from previous solution
        TRAVEL_TIMES = effective_travel_times.copy()
        print("   📏 Using EFFECTIVE travel times from previous iteration")
        # Report average congestion factor
        avg_factor = np.mean([TRAVEL_TIMES[a] / FFTT[a] for a in ARCS if FFTT[a] > 0])
        print(f"   📊 Average congestion factor: {avg_factor:.3f}")
    
    def arc_duration_slots(i, j):
        # Use TRAVEL_TIMES instead of FFTT for cell occupancy
        tt_min = TRAVEL_TIMES[(i, j)]
        return max(1, int(math.ceil(tt_min / DELTA_MIN)))
    
    ARC_DURATION = {(i, j): arc_duration_slots(i, j) for (i, j) in ARCS}

    # Load Background Traffic
    z_path = "dati/traffic_DEF_N.json"
    if not pathlib.Path(z_path).exists():
        raise FileNotFoundError(f"❌ Background traffic file {z_path} not found")
    with open(z_path, "r", encoding="utf-8") as f:
        traffic_data = json.load(f)

    Z = {}
    clips = 0
    for arc_key, d in traffic_data.items():
        try:
            i, j = [s.strip() for s in arc_key.split(",")]
            i, j = str(i), str(j)
            if (i, j) not in CAPACITY:
                continue
            mu = CAPACITY[(i, j)]
            z_cap = max(0.0, u_max * mu - 2.0)
            for t in TIME_SLOTS:
                val = float(d.get(str(t), 0.0)) * Z_SCALE
                if val > z_cap:
                    val = z_cap
                    clips += 1
                Z[((i, j), t)] = val
        except:
            pass

    total_Z = sum(Z.values())
    print(f"✂️ Z clipped on {clips} cells")
    print(f"📊 Total background traffic: {total_Z:,.0f}")

    # Parse Trips - NOW USING TRAVEL_TIMES INSTEAD OF FFTT
    TRIPS, PATHS_PER_TRIP, TRIPS_DATA = [], {}, {}
    total_demand = 0.0
    for _, row in df_trips.iterrows():
        c = int(row["trip_id"])
        demand = float(row["demand"])
        total_demand += demand
        paths = []
        k = 0
        while f"path_{k}" in row:
            pstr = row.get(f"path_{k}", None)
            tcol = f"tempo_{k}"
            if pd.isna(pstr) or tcol not in row or pd.isna(row[tcol]):
                break
            
            arcs_on_path = _parse_path_string(pstr)
            if not arcs_on_path:
                k += 1
                continue
            
            # ============================================================
            # KEY CHANGE: Calculate path time using TRAVEL_TIMES
            # ============================================================
            path_time = sum(TRAVEL_TIMES[(i, j)] for (i, j) in arcs_on_path)
            
            dep_col = f"possible_departure_times_{k}"
            dep_times = _parse_int_list(row.get(dep_col, ""))
            pref_col = f"preferenza_{k}"
            pref = str(row.get(pref_col, "entrambi")).strip()
            if dep_times:
                paths.append({
                    "arcs": arcs_on_path, 
                    "time": path_time,  # Now uses effective times
                    "dep_times": sorted(set(dep_times)), 
                    "pref": pref
                })
            k += 1
        if paths:
            TRIPS.append(c)
            PATHS_PER_TRIP[c] = list(range(len(paths)))
            TRIPS_DATA[c] = {"demand": demand, "paths": paths}

    # ============================================================
    # COMPUTE SCALING FACTOR
    # ============================================================
    typical_flow = total_demand / max(len(ARCS), 1) / max(len(TIME_SLOTS), 1)
    typical_ff = np.mean([FFTT[a] for a in ARCS]) if ARCS else 1.0
    typical_mu = np.mean([CAPACITY[a] for a in ARCS]) if ARCS else 1.0
    
    typical_sigma = bpr_sigma_arc(typical_ff, typical_mu, typical_flow)
    typical_obj_raw = typical_sigma * len(ARCS) * len(TIME_SLOTS)
    
    TARGET_SCALE = 1e6
    OBJ_SCALE = TARGET_SCALE / max(typical_obj_raw, 1.0)
    
    print(f"\n🔢 SCALING ANALYSIS:")
    print(f"   Typical flow per cell: {typical_flow:.1f}")
    print(f"   Typical raw Beckmann: {typical_obj_raw:.2e}")
    print(f"   Objective scale factor: {OBJ_SCALE:.2e}")
    print(f"   Target objective: O({TARGET_SCALE:.0e})")

    # ============================================================
    # Filter Options - NOW USING TRAVEL_TIMES
    # ============================================================
    min_travel_times = {c: min(p["time"] for p in TRIPS_DATA[c]["paths"]) for c in TRIPS}
    ctp_set = []
    for c in TRIPS:
        for p_idx, pdata in enumerate(TRIPS_DATA[c]["paths"]):
            # Filter based on GAMMA using TRAVEL_TIMES
            if pdata["time"] > (1.0 + GAMMA) * min_travel_times[c]:
                continue
            pref = pdata.get("pref", "entrambi")
            for tau in pdata["dep_times"]:
                if pref == "giorno1" and tau >= 52:
                    continue
                if pref == "giorno2" and tau <= 51:
                    continue
                offset = 0
                ok = True
                for (i, j) in pdata["arcs"]:
                    dur = ARC_DURATION[(i, j)]
                    t_start = tau + offset
                    t_end = t_start + dur - 1
                    if t_start < 0 or t_end > TIME_SLOTS[-1]:
                        ok = False
                        break
                    offset += dur
                if ok:
                    ctp_set.append((c, p_idx, tau))

    print(f"🔧 [CTP] Options: {len(ctp_set):,} (GAMMA={GAMMA})")
    if len(ctp_set) == 0:
        raise ValueError("ERROR: No options available")

    PATH_ARCS = {(c, p_idx): list(pdata["arcs"])
                 for c in TRIPS for p_idx, pdata in enumerate(TRIPS_DATA[c]["paths"])}

    # PWL with SCALING
    H = int(os.getenv("PWL_SEGMENTS", "10"))
    pwl_data = {}

    for (i, j) in ARCS:
        mu_slot = CAPACITY[(i, j)]
        ff_arc = FFTT[(i, j)]
        dur = ARC_DURATION[(i, j)]
        ff_cell = ff_arc / dur
        
        bmax = max(1e-6, u_max * mu_slot)
        bpts = np.linspace(0.0, bmax, H + 1)
        seglen = np.diff(bpts)

        def sigma_arc(x): return bpr_sigma_arc(ff_arc, mu_slot, x)
        def lat_arc(x): return bpr_latency_arc(ff_arc, mu_slot, x)
        
        kappa_cell = []
        kappa_u_cell = []
        for h_idx in range(H):
            a, b = bpts[h_idx], bpts[h_idx+1]
            ds = max(1e-6, b - a)
            
            # Beckmann slope WITH SCALING
            sig_a, sig_b = sigma_arc(a), sigma_arc(b)
            slope_raw = (sig_b - sig_a) / ds / dur
            slope_scaled = slope_raw * OBJ_SCALE
            kappa_cell.append(max(slope_scaled, 1e-9))
            
            # Latency slope (NO scaling)
            u_a, u_b = lat_arc(a) / dur, lat_arc(b) / dur
            u_slope = (u_b - u_a) / ds
            kappa_u_cell.append(max(u_slope, 0.0))

        pwl_data[(i, j)] = {
            "bpts": bpts,
            "seglen": seglen,
            "kappa": kappa_cell,
            "kappa_u": kappa_u_cell,
            "u0": ff_cell,
            "dur": dur
        }

    USE_PREFIX = os.getenv("PWL_PREFIX", "0") == "1"
    print(f"🧩 PWL: {H} segments, prefix={'ON' if USE_PREFIX else 'OFF'}")

    # Pyomo Model
    model = ConcreteModel()
    model.A = Set(initialize=ARCS, dimen=2)
    model.T = Set(initialize=TIME_SLOTS)
    model.C = Set(initialize=TRIPS)
    model.PATHS = Set(model.C, initialize=PATHS_PER_TRIP)
    model.CTP = Set(initialize=ctp_set, dimen=3)

    model.fftt = Param(model.A, initialize=FFTT)
    model.mu = Param(model.A, initialize=CAPACITY)
    model.dur = Param(model.A, initialize=ARC_DURATION)
    model.dem = Param(model.C, initialize={c: TRIPS_DATA[c]["demand"] for c in TRIPS})
    model.Z = Param(model.A, model.T, initialize=lambda m,i,j,t: Z.get(((i,j),t), 0.0))
    model.u_max = Param(initialize=u_max)
    model.OBJ_SCALE = Param(initialize=OBJ_SCALE, mutable=False)

    # Variables
    model.y = Var(model.CTP, domain=NonNegativeReals, initialize=0.0)
    model.x = Var(model.A, model.T, domain=NonNegativeReals, initialize=0.0)
    model.eta = Var(model.A, model.T, domain=NonNegativeReals, initialize=0.0)
    model.u_lat = Var(model.A, model.T, domain=NonNegativeReals, initialize=0.0)
    model.TT = Var(model.CTP, domain=NonNegativeReals, initialize=0.0)
    model.I = Var(model.CTP, domain=NonNegativeReals, initialize=1.0)

    Hset = list(range(1, H + 1))
    model.Hset = Set(initialize=Hset)
    model.lmbd = Var(model.A, model.T, model.Hset, domain=NonNegativeReals, initialize=0.0)

    # Soft demand with SCALED penalty
    model.r = Var(model.C, domain=NonNegativeReals, initialize=0.0)
    PEN_DEM_RAW = float(os.getenv("PEN_DEM", "1e5"))
    PEN_DEM = PEN_DEM_RAW * OBJ_SCALE
    print(f"🔧 Soft demand penalty (scaled): {PEN_DEM:.2e}")

    # Constraints
    def x_def_rule(m, i, j, t):
        return m.x[i, j, t] == sum(m.lmbd[i, j, t, h] for h in m.Hset)
    model.x_def = Constraint(model.A, model.T, rule=x_def_rule)

    def lambda_bounds_rule(m, i, j, t, h):
        seglen = pwl_data[(i, j)]["seglen"][h - 1]
        return m.lmbd[i, j, t, h] <= seglen
    model.lambda_bounds = Constraint(model.A, model.T, model.Hset, rule=lambda_bounds_rule)

    if USE_PREFIX:
        def prefix_rule(m, i, j, t, h):
            b_h = pwl_data[(i, j)]["bpts"][h]
            return sum(m.lmbd[i, j, t, s] for s in range(1, h + 1)) <= b_h
        model.prefix = Constraint(model.A, model.T, model.Hset, rule=prefix_rule)

    def eta_def_rule(m, i, j, t):
        ks = pwl_data[(i, j)]["kappa"]
        return m.eta[i, j, t] == sum(ks[h - 1] * m.lmbd[i, j, t, h] for h in m.Hset)
    model.eta_def = Constraint(model.A, model.T, rule=eta_def_rule)

    def u_def_rule(m, i, j, t):
        ku = pwl_data[(i, j)]["kappa_u"]
        u0 = pwl_data[(i, j)]["u0"]
        return m.u_lat[i, j, t] == u0 + sum(ku[h - 1] * m.lmbd[i, j, t, h] for h in m.Hset)
    model.u_def = Constraint(model.A, model.T, rule=u_def_rule)

    # TTI cap
    RELAX_TTI = os.getenv("RELAX_TTI", "1") == "1"
    if RELAX_TTI:
        model.slack_tti = Var(model.A, model.T, domain=NonNegativeReals, initialize=0.0)
        PEN_TTI_RAW = float(os.getenv("PEN_TTI", "1e3"))
        PEN_TTI = PEN_TTI_RAW * OBJ_SCALE
        def tti_bound_rule(m, i, j, t):
            return m.x[i, j, t] <= m.u_max * m.mu[i, j] + m.slack_tti[i, j, t]
        model.tti_bound = Constraint(model.A, model.T, rule=tti_bound_rule)
        print(f"🔧 TTI penalty (scaled): {PEN_TTI:.2e}")
    else:
        PEN_TTI = 0.0
        def tti_bound_rule(m, i, j, t):
            return m.x[i, j, t] <= m.u_max * m.mu[i, j]
        model.tti_bound = Constraint(model.A, model.T, rule=tti_bound_rule)

    # Demand
    def demand_rule(m, c):
        lhs = sum(m.y[c, p, tau] for (cc, p, tau) in m.CTP if cc == c)
        return lhs + m.r[c] == m.dem[c]
    model.demand = Constraint(model.C, rule=demand_rule)

    # Incidence
    arc_time_to_options = defaultdict(list)
    tt_cells_map = defaultdict(list)

    def get_occupied_cells(c, p, tau):
        cells = []
        offset = 0
        for (i, j) in PATH_ARCS[(c, p)]:
            dur = ARC_DURATION[(i, j)]
            for d in range(dur):
                t_use = tau + offset + d
                if t_use < 0 or t_use > TIME_SLOTS[-1]:
                    return None
                cells.append((i, j, t_use))
            offset += dur
        return cells

    for (c, p, tau) in ctp_set:
        cells = get_occupied_cells(c, p, tau)
        if cells is None:
            continue
        tt_cells_map[(c, p, tau)] = cells
        for (i, j, t) in cells:
            arc_time_to_options[(i, j, t)].append((c, p, tau))

    def flow_rule(m, i, j, t):
        options = arc_time_to_options.get((i, j, t), [])
        return m.x[i, j, t] == m.Z[i, j, t] + sum(m.y[c, p, tau] for (c, p, tau) in options)
    model.flow = Constraint(model.A, model.T, rule=flow_rule)

    def tt_proxy_rule(m, c, p, tau):
        cells = tt_cells_map[(c, p, tau)]
        return m.TT[c, p, tau] == sum(m.u_lat[i, j, t] for (i, j, t) in cells)
    model.path_travel_time = Constraint(model.CTP, rule=tt_proxy_rule)

    freeflow_tt_map = {}
    for c in TRIPS:
        for p in PATHS_PER_TRIP[c]:
            freeflow_tt_map[(c, p)] = sum(FFTT[(i, j)] for (i, j) in PATH_ARCS[(c, p)])
    
    def inconvenience_rule(m, c, p, tau):
        denom = freeflow_tt_map[(c, p)]
        if denom > 1e-9:
            return m.I[c, p, tau] * denom == m.TT[c, p, tau]
        else:
            return m.I[c, p, tau] == 1.0
    model.inconvenience = Constraint(model.CTP, rule=inconvenience_rule)

    def I_floor_rule(m, c, p, tau):
        return m.I[c, p, tau] >= 0.99
    model.I_floor = Constraint(model.CTP, rule=I_floor_rule)

    # Objectives (with scaled penalties)
    tti_penalty = PEN_TTI * sum(model.slack_tti[i,j,t] for (i,j) in model.A for t in model.T) if RELAX_TTI else 0.0
    demand_penalty = PEN_DEM * sum(model.r[c] for c in model.C)
    
    model.TSTT_total = Expression(expr=sum(model.eta[i, j, t] for (i, j) in model.A for t in model.T))
    
    model.obj_TSTT = Objective(
        expr=model.TSTT_total + demand_penalty + tti_penalty,
        sense=minimize
    )

    model.obj_inconv = Objective(
        expr=sum(model.I[c, p, tau] * model.y[c, p, tau] for (c, p, tau) in model.CTP),
        sense=minimize
    )
    model.obj_inconv.deactivate()
    
    model.PEN_DEM = Param(initialize=PEN_DEM, mutable=False)
    model.PEN_TTI = Param(initialize=PEN_TTI if RELAX_TTI else 0.0, mutable=False)

    model.TSTT_star = Param(initialize=0.0, mutable=True)
    def eps_cap_rule(m):
        return m.TSTT_total <= (1.0 + EPSILON) * m.TSTT_star
    model.eps_cap = Constraint(rule=eps_cap_rule)
    model.eps_cap.deactivate()

    print("✅ Model created with SCALED coefficients")
    print(f"   Expected objective: O({TARGET_SCALE:.0e})")
    
    return model, TRIPS_DATA, ARCS, TIME_SLOTS, FFTT, CAPACITY, Z, PATH_ARCS, GAMMA, total_demand, OBJ_SCALE, TRAVEL_TIMES


def compute_effective_travel_times(model, ARCS, TIME_SLOTS, FFTT, CAPACITY):
    """
    Compute effective (congested) travel times from the current solution.
    Returns a dictionary mapping (i,j) -> average effective travel time.
    """
    print("\n" + "=" * 60)
    print("📊 COMPUTING EFFECTIVE TRAVEL TIMES")
    print("=" * 60)
    
    effective_times = {}
    
    for (i, j) in ARCS:
        ff = FFTT[(i, j)]
        mu = CAPACITY[(i, j)]
        
        # Collect all flows on this arc across time
        flows = []
        for t in TIME_SLOTS:
            try:
                x_val = value(model.x[i, j, t], exception=False)
                if x_val is not None and x_val > 0:
                    flows.append(x_val)
            except:
                pass
        
        if not flows:
            # No traffic on this arc
            effective_times[(i, j)] = ff
            continue
        
        # Compute average flow
        avg_flow = np.mean(flows)
        
        # Compute effective travel time using BPR
        eff_time = bpr_latency_arc(ff, mu, avg_flow)
        effective_times[(i, j)] = eff_time
        
        # Report if significantly congested
        congestion_factor = eff_time / ff
        if congestion_factor > 1.5:
            print(f"   Arc ({i},{j}): FF={ff:.1f}min, Eff={eff_time:.1f}min (x{congestion_factor:.2f})")
    
    # Report statistics
    all_factors = [effective_times[a] / FFTT[a] for a in ARCS if FFTT[a] > 0]
    print(f"\n   Average congestion factor: {np.mean(all_factors):.3f}")
    print(f"   Max congestion factor: {np.max(all_factors):.3f}")
    print(f"   Arcs with >50% delay: {sum(1 for f in all_factors if f > 1.5)}")
    
    return effective_times