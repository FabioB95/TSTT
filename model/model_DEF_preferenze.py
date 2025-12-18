import json
from pyomo.environ import *
from collections import defaultdict

# === Caricamento dati ===
with open("dati/nodes.json") as f:
    nodes_data = json.load(f)["nodes"]

with open("dati/arcs_bidirectional.json") as f:
    arcs_data = json.load(f)["edges"]

with open("dati/trips_with_paths_temporal.json") as f:
    trips_data = json.load(f)["trips"]

with open("dati/traffic_DEF.json") as f:
    traffic_data_raw = json.load(f)

with open("dati/linearization_DEF.json") as f:
    lin_data = json.load(f)

with open("dati/c_cost_DEF.json") as f:
    c_cost_data = json.load(f)

with open("dati/c_cost_FP_DEF.json") as f:
    c_cost_FF = json.load(f)

print("\n✅ Dati caricati!")

# === Set base ===
NODES = [n["ID"] for n in nodes_data]
ARCS = [(a["from_node"], a["to_node"]) for a in arcs_data]

TIME = list(range(1, 50))  # esempio

TRIPS = list(range(len(trips_data)))

max_paths_per_trip = max(len(trip["paths"]) for trip in trips_data)
PATHS_RANGE = list(range(max_paths_per_trip))

print("\n✅ Set base caricati!")

# === Parametri archi ===
FFTT = {(a["from_node"], a["to_node"]): (float(a["distance"]) / float(a["maxspeed"])) * 60 for a in arcs_data}
CAPACITY = {(a["from_node"], a["to_node"]): float(a["capacity"]) for a in arcs_data}

# Conversione dati traffico da minuti a snapshot index
Z = {}
for arc_key, time_dict in traffic_data_raw.items():
    i, j = arc_key.split(",")
    for t_min_str, forecast in time_dict.items():
        t_min = int(t_min_str)
        t_snapshot = (t_min - 360) // 30 + 1
        if t_snapshot in TIME:
            Z[(i, j, t_snapshot)] = forecast

print("\n✅ Parametri archi caricati!")

# === Parametri linearizzazione ===
breakpoints = {}
tti_values = {}
H_data = {}
for key, val in lin_data.items():
    i, j = key.split("_")
    a = (i, j)
    bp = val["breakpoints"]
    tti = val["tti_values"]
    H_data[a] = list(range(1, len(bp)))
    for h in H_data[a]:
        breakpoints[a, h] = (bp[h-1], bp[h])
        tti_values[a, h] = (tti[h-1], tti[h])

print("\n✅ Parametri linearizzazione caricati!")

# === Parametro tempo ideale partenza per trip ===
ideal_departure_time = {
    c: min(
        min(path["possible_departure_times"]) 
        for path in trips_data[c]["paths"]
    )
    for c in TRIPS
}

print("\n✅ Tempi ideali di partenza caricati!")

# === Costruzione modello Pyomo ===
model = ConcreteModel()
model.A = Set(initialize=ARCS, dimen=2)
model.T = Set(initialize=TIME)
model.C = Set(initialize=TRIPS)
model.P = Set(initialize=PATHS_RANGE)

model.H = Param(model.A, initialize=H_data, default=[])

# Parametri trip
DEMAND = {c: trips_data[c]["demand"] for c in TRIPS}
model.dem = Param(model.C, initialize=DEMAND)
model.fftt = Param(model.A, initialize=FFTT)
model.mu = Param(model.A, initialize=CAPACITY)
model.Z = Param(model.A * model.T, initialize=Z, default=0)

# Tempo ideale per trip
model.t_ideal = Param(model.C, initialize=ideal_departure_time)

# CTP set (trip, path, tau)
ctp_set_temp = []
for c in TRIPS:
    for p, path in enumerate(trips_data[c]["paths"]):
        for tau in path["possible_departure_times"]:
            tau_int = int(tau)
            if tau_int in TIME and p in PATHS_RANGE:
                ctp_set_temp.append((c, p, tau_int))
model.CTP = Set(initialize=ctp_set_temp, dimen=3)



# Nuova definizione delay_val basata su departure_times
delay_val = {}
for (c, p, t) in model.CTP:
    preferred_times = trips_data[c].get("departure_times", [])
    if not preferred_times:
        delay = 100  # Penalità alta se mancano dati
    else:
        delay = min(abs(t - int(pt)) for pt in preferred_times)
    delay_val[(c, p, t)] = delay

# Associa come parametro Pyomo
model.delay_val = Param(model.CTP, initialize=delay_val, default=100)



# Linearizzazione parametri
ATH = []
for (i, j) in model.A:
    for t in model.T:
        for h in model.H[(i, j)]:
            ATH.append((i, j, t, h))
model.ATH = Set(dimen=4, initialize=ATH)

model.lmbda = Var(model.ATH, domain=NonNegativeReals)
model.b_prev = Param(model.ATH, initialize=lambda m, i, j, t, h: breakpoints[(i,j),h][0])
model.b = Param(model.ATH, initialize=lambda m, i, j, t, h: breakpoints[(i,j),h][1])
model.tti_h = Param(model.ATH, initialize=lambda m, i, j, t, h: tti_values[(i,j),h][1])
model.tti_h_prev = Param(model.ATH, initialize=lambda m, i, j, t, h: tti_values[(i,j),h][0])

# Variabili decisione
model.y = Var(model.CTP, domain=NonNegativeReals)
model.x = Var(model.A * model.T, domain=NonNegativeReals)
model.sigma = Var(model.A * model.T, domain=NonNegativeReals)

# Costi
# === Costi ===
# Per c_cost_DEF.json (formato "tripId_pathId_departureTime")
raw_c_cost_parsed = {}
for k, v in c_cost_data.items():
    try:
        parts = k.split('_')
        if len(parts) < 3:
            print(f"Formato chiave non supportato: {k}")
            continue
            
        c_val = int(parts[0])
        p_val = int(parts[1])
        tau_val = int(parts[2])
        raw_c_cost_parsed[(c_val, p_val, tau_val)] = v
        
    except (ValueError, IndexError) as e:
        print(f"Errore nel parsing della chiave {k}: {str(e)}")

# Filtraggio per gli elementi presenti nel modello
COST_filtered = {}
for (c, p, tau) in model.CTP:
    key = (c, p, tau)
    if key in raw_c_cost_parsed:
        COST_filtered[key] = raw_c_cost_parsed[key]
    else:
        # Valore di default alto per combinazioni mancanti
        COST_filtered[key] = 999999

# Per c_cost_FP_DEF.json (formato semplice "tripId")
raw_c_cost_FF_parsed = {}
for k, v in c_cost_FF.items():
    try:
        c_id = int(k)  # Conversione diretta della chiave
        raw_c_cost_FF_parsed[c_id] = v
    except ValueError:
        print(f"Errore nel parsing della chiave FF: {k}")

# Filtraggio per gli elementi presenti nel modello
COST_FF_filtered = {}
for c_id in model.C:
    if c_id in raw_c_cost_FF_parsed:
        COST_FF_filtered[c_id] = raw_c_cost_FF_parsed[c_id]
    else:
        # Valore di default per trip mancanti
        COST_FF_filtered[c_id] = 1

# === Aggiornamento parametri modello ===
model.c_cost = Param(model.CTP, initialize=COST_filtered, default=999999)
model.fftt_c = Param(model.C, initialize=COST_FF_filtered, default=1)

# === Correzione warning Param H ===
model.H = Param(model.A, initialize=H_data, within=Any, default=[])


COST_filtered = {}
for (c, p, tau) in model.CTP:
    if (c, p, tau) in raw_c_cost_parsed:
        COST_filtered[(c,p,tau)] = raw_c_cost_parsed[(c,p,tau)]
model.c_cost = Param(model.CTP, initialize=COST_filtered, default=999999)



# --- Parametro PI ---
PI = defaultdict(int)
for c in TRIPS:
    for p, path in enumerate(trips_data[c]["paths"]):
        arcs = [(a[0], a[1]) for a in path["arcs"]]
        fftts = path["base_times"]
        for tau in path["possible_departure_times"]:
            t = int(tau)
            for (a, tt) in zip(arcs, fftts):
                for offset in range(tt):
                    snapshot = t + offset
                    if snapshot in model.T:
                        PI[c, p, t, a, snapshot] = 1

# === Vincoli ===

def demand_rule(m, c):
    return sum(m.y[c_idx, p, tau] for (c_idx, p, tau) in m.CTP if c_idx == c) == m.dem[c]
model.demand_satisfied = Constraint(model.C, rule=demand_rule)

def flow_rule(m, i, j, t):
    return m.x[i, j, t] == m.Z[i, j, t] + sum(
        PI[c, p, tau_dep, (i, j), t] * m.y[c, p, tau_dep]
        for (c, p, tau_dep) in m.CTP if (c, p, tau_dep, (i, j), t) in PI
    )
model.flow_def = Constraint(model.A * model.T, rule=flow_rule)

def lambda_sum_rule(m, i, j, t):
    return m.x[i, j, t] == sum(m.lmbda[i, j, t, h] for h in m.H[(i, j)])
model.lambda_sum = Constraint(model.A * model.T, rule=lambda_sum_rule)

def sigma_def_rule(m, i, j, t):
    return m.sigma[i, j, t] == 1 + sum(
        ((m.tti_h[i, j, t, h] - m.tti_h_prev[i, j, t, h]) /
         (m.b[i, j, t, h] - m.b_prev[i, j, t, h])) * m.lmbda[i, j, t, h]
        for h in m.H[(i, j)]
    )
model.sigma_def = Constraint(model.A * model.T, rule=sigma_def_rule)

def enforce_lambda_if_flow(m, i, j, t, h):
    return m.lmbda[i, j, t, h] <= m.x[i, j, t]
model.lambda_bound = Constraint(model.ATH, rule=enforce_lambda_if_flow)

def arc_capacity_rule(m, i, j, t):
    return m.x[i, j, t] <= 10 * m.mu[i, j]
model.arc_capacity = Constraint(model.A * model.T, rule=arc_capacity_rule)

# Limite massimo veicoli per tempo (esempio 30% della domanda totale)
def time_distribution_rule(m, t_snapshot):
    max_vehicles_per_time = sum(m.dem[c] for c in m.C) * 0.3
    return sum(m.y[c, p, tau] for (c, p, tau) in m.CTP if tau == t_snapshot) <= max_vehicles_per_time
model.time_distribution = Constraint(model.T, rule=time_distribution_rule)



ALPHA = 2.0
def tti_bound_rule(m, i, j, t):
    return m.sigma[i, j, t] <= ALPHA
model.tti_bound = Constraint(model.A * model.T, rule=tti_bound_rule)

print("\n✅ Vincoli caricati!")

# === Funzione obiettivo con penalità ritardo ===
penalty_weight = 1000.0  # penalitá

model.obj = Objective(
    expr=sum(
        (model.c_cost[c, p, t] / model.fftt_c[c]) * model.y[c, p, t]
        + penalty_weight * model.delay_val[c, p, t] * model.y[c, p, t]
        for (c, p, t) in model.CTP
    ),
    sense=minimize
)


print("\n✅ Modello pronto!")
