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

with open("dati/linearization_test2.json") as f:
    lin_data = json.load(f)

with open("dati/c_cost_test2.json") as f:
    c_cost_data = json.load(f)

with open("dati/c_cost_FP_test2.json") as f:
    c_cost_FF = json.load(f)

print("\n✅Dati caricati!")

# === Set base ===
NODES = [n["ID"] for n in nodes_data]
ARCS = [(a["from_node"], a["to_node"]) for a in arcs_data]

# Assuming TIME covers all necessary 'tau' and 'snapshot' values
TIME = list(range(1, 50)) 

TRIPS = list(range(len(trips_data)))

# Calculate the maximum number of paths for any trip
max_paths_per_trip = 0
for c in TRIPS:
    max_paths_per_trip = max(max_paths_per_trip, len(trips_data[c]["paths"]))
PATHS_RANGE = list(range(max_paths_per_trip)) # This will be the set for model.P

print("\n✅Set base caricato!")

# === Parametri arc ===
FFTT = {(a["from_node"], a["to_node"]): (float(a["distance"]) / float(a["maxspeed"])) * 60 for a in arcs_data}
CAPACITY = {(a["from_node"], a["to_node"]): float(a["capacity"]) for a in arcs_data}

# Conversione dati traffico da formato minuti a snapshot index
Z = {}
for arc_key, time_dict in traffic_data_raw.items():
    i, j = arc_key.split(",")
    for t_min_str, forecast in time_dict.items():
        t_min = int(t_min_str)
        t_snapshot = (t_min - 360) // 30 + 1
        if t_snapshot in TIME:
            Z[(i, j, t_snapshot)] = forecast

print("\n✅Parametri arc caricati!")

# === Parametri linearizzazione ===
# These Python dictionaries need to be defined before model.Param uses them
breakpoints = {}
tti_values = {}
H_data = {} # Renamed H to H_data to avoid confusion with model.H later
for key, val in lin_data.items():
    i, j = key.split("_")
    a = (i, j)
    bp = val["breakpoints"]
    tti = val["tti_values"]
    H_data[a] = list(range(1, len(bp))) # This is the Python dictionary for H
    for h in H_data[a]: # Iterate over the breakpoints indices for this arc
        breakpoints[a, h] = (bp[h-1], bp[h])
        tti_values[a, h] = (tti[h-1], tti[h])

print("\n✅Parametri linearizzazione caricati!")

# === Pyomo model ===
model = ConcreteModel()
model.A = Set(initialize=ARCS, dimen=2)
model.T = Set(initialize=TIME)
model.C = Set(initialize=TRIPS)
model.P = Set(initialize=PATHS_RANGE) # model.P is now defined!

# Define model.H here as a Pyomo Param using the H_data dictionary
model.H = Param(model.A, initialize=H_data, default=[]) 

print("\n✅Pyomo caricati!")

# === Parametri dei trip ===
DEMAND = {c: trips_data[c]["demand"] for c in TRIPS}
model.dem = Param(model.C, initialize=DEMAND)
model.fftt = Param(model.A, initialize=FFTT)
model.mu = Param(model.A, initialize=CAPACITY)
model.Z = Param(model.A * model.T, initialize=Z, default=0)

print("\n✅Parametri trip caricati!")

# === CTP ===
ctp_set_temp = []
for c in TRIPS:
    for p, path in enumerate(trips_data[c]["paths"]):
        for tau in path["possible_departure_times"]:
            if int(tau) in TIME and p in PATHS_RANGE:
                ctp_set_temp.append((c, p, int(tau)))

model.CTP = Set(initialize=ctp_set_temp, dimen=3)

print("\n✅CTP caricati!")

# === π_cpτ^{at} ===
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

print("\n✅PI caricati!")

# === Linearizzazione Pyomo ===
# Now model.H is correctly defined as a Param, so we can use it.
ATH = []
for (i, j) in model.A:
    for t in model.T:
        for h in model.H[(i, j)]: # Access model.H as a Param now
            ATH.append((i, j, t, h))
model.ATH = Set(dimen=4, initialize=ATH)


model.lmbda = Var(model.ATH, domain=NonNegativeReals)

model.b_prev = Param(model.ATH, initialize=lambda m, i, j, t, h: breakpoints[(i, j), h][0])
model.b = Param(model.ATH, initialize=lambda m, i, j, t, h: breakpoints[(i, j), h][1])
model.tti_h = Param(model.ATH, initialize=lambda m, i, j, t, h: tti_values[(i, j), h][1])
model.tti_h_prev = Param(model.ATH, initialize=lambda m, i, j, t, h: tti_values[(i, j), h][0])

print("\n✅Parametri linearizzazione caricati!")

# === Variabili ===
model.y = Var(model.CTP, domain=NonNegativeReals)
model.x = Var(model.A * model.T, domain=NonNegativeReals)
model.sigma = Var(model.A * model.T, domain=NonNegativeReals)

# === Costi ===
raw_c_cost_parsed = {(int(k.split("_")[1]), int(k.split("_")[2]), int(k.split("_")[3])): v for k, v in c_cost_data.items()}

COST_filtered = {}
for (c, p, tau) in model.CTP:
    if (c, p, tau) in raw_c_cost_parsed:
        COST_filtered[(c, p, tau)] = raw_c_cost_parsed[(c, p, tau)]

model.c_cost = Param(model.CTP, initialize=COST_filtered, default=999999)

raw_c_cost_FF_parsed = {int(k.split("_")[1]): v for k, v in c_cost_FF.items()}

COST_FF_filtered = {}
for c_id in model.C:
    if c_id in raw_c_cost_FF_parsed:
        COST_FF_filtered[c_id] = raw_c_cost_FF_parsed[c_id]

model.fftt_c = Param(model.C, initialize=COST_FF_filtered, default=1)

print("\n✅Parametri, costi, variabili caricati!")

# === Vincoli ===

def demand_rule(m, c):
    return sum(m.y[c_idx, p, tau] for (c_idx, p, tau) in m.CTP if c_idx == c) == m.dem[c]
model.demand_satisfied = Constraint(model.C, rule=demand_rule)

print("\n✅demand_rule")

def flow_rule(m, i, j, t):
    return m.x[i, j, t] == m.Z[i, j, t] + sum(
        PI[c, p, tau_dep, (i, j), t] * m.y[c, p, tau_dep]
        for (c, p, tau_dep) in m.CTP if (c, p, tau_dep, (i, j), t) in PI
    )
model.flow_def = Constraint(model.A * model.T, rule=flow_rule)

print("\n✅flow_rule")

def lambda_sum_rule(m, i, j, t):
    return m.x[i, j, t] == sum(m.lmbda[i, j, t, h] for h in m.H[(i, j)]) # Use model.H directly
model.lambda_sum = Constraint(model.A * model.T, rule=lambda_sum_rule)

print("\n✅lambda_sum_rule")

def sigma_def_rule(m, i, j, t):
    return m.sigma[i, j, t] == 1 + sum(
        ((m.tti_h[i, j, t, h] - m.tti_h_prev[i, j, t, h]) /
         (m.b[i, j, t, h] - m.b_prev[i, j, t, h])) * m.lmbda[i, j, t, h]
        for h in m.H[(i, j)] # Use model.H directly
    )
model.sigma_def = Constraint(model.A * model.T, rule=sigma_def_rule)

print("\n✅sigma_def_rule")

def enforce_lambda_if_flow(m, i, j, t, h):
    return m.lmbda[i, j, t, h] <= m.x[i, j, t]
model.lambda_bound = Constraint(model.ATH, rule=enforce_lambda_if_flow)

print("\n✅lambda_bound")

def arc_capacity_rule(m, i, j, t):
    return m.x[i, j, t] <= 10 * m.mu[i, j]
model.arc_capacity = Constraint(model.A * model.T, rule=arc_capacity_rule)

print("\n✅arc_capacity")

def time_distribution_rule(m, t_snapshot):
    max_vehicles_per_time = sum(m.dem[c] for c in m.C) * 0.3
    return sum(m.y[c, p, tau] for (c, p, tau) in m.CTP if t_snapshot == tau) <= max_vehicles_per_time
model.time_distribution = Constraint(model.T, rule=time_distribution_rule)

print("\n✅time_distribution_rule")

ALPHA = 2.0
def tti_bound_rule(m, i, j, t):
    return m.sigma[i, j, t] <= ALPHA
model.tti_bound = Constraint(model.A * model.T, rule=tti_bound_rule)

print("\n✅Vincoli caricati!")

# === Funzione obiettivo ===
epsilon = 0.0001
model.obj = Objective(
    expr=sum((model.c_cost[c, p, tau] / model.fftt_c[c]) * model.y[c, p, tau] for (c, p, tau) in model.CTP),
    sense=minimize
)

print("\n✅Fatto!")