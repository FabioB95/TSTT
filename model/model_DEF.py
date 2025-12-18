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
    traffic_data = json.load(f)

with open("dati/linearization_DEF.json") as f:
    lin_data = json.load(f)

# === Set base ===
NODES = [n["ID"] for n in nodes_data]
ARCS = [(a["from_node"], a["to_node"]) for a in arcs_data]
TIME = list(range(1, 108))
TRIPS = list(range(len(trips_data)))
PATHS_PER_TRIP = {c: list(range(len(trips_data[c]["paths"]))) for c in TRIPS}

# === Parametri archi ===
FFTT = {}
CAPACITY = {}
for a in arcs_data:
    i, j = a["from_node"], a["to_node"]
    distance = float(a["distance"])
    speed = float(a["maxspeed"])
    fftt = (distance / speed) * 60 if speed > 0 else 9999
    FFTT[(i, j)] = round(fftt, 3)
    CAPACITY[(i, j)] = float(a["capacity"])

Z = {(i, j, int(t)): val[str(t)] for (key, val) in traffic_data.items() for i, j in [key.split(",")] for t in val}

# === Parametri linearizzazione ===
breakpoints, tti_values, H = {}, {}, {}
for key, val in lin_data.items():
    i, j = key.split("_")
    a = (i, j)
    bp = val["breakpoints"]
    tti = val["tti_values"]
    H[a] = list(range(1, len(bp)))
    for h in H[a]:
        breakpoints[a, h] = (bp[h - 1], bp[h])
        tti_values[a, h] = (tti[h - 1], tti[h])

# === Pyomo model ===
model = ConcreteModel()
model.A = Set(initialize=ARCS, dimen=2)
model.T = Set(initialize=TIME)
model.C = Set(initialize=TRIPS)
model.PATHS = Set(model.C, initialize=PATHS_PER_TRIP)
model.fftt = Param(model.A, initialize=FFTT)
model.mu = Param(model.A, initialize=CAPACITY)
model.A_T = Set(dimen=3, initialize=Z.keys())
model.Z = Param(model.A_T, initialize=Z, default=0)

# === Domanda ===
DEMAND = {c: trips_data[c]["demand"] for c in TRIPS}
model.dem = Param(model.C, initialize=DEMAND)
ctp_set = [(c, p, int(tau)) for c in TRIPS for p, path in enumerate(trips_data[c]["paths"]) for tau in path["possible_departure_times"]]
model.CTP = Set(initialize=ctp_set, dimen=3)

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
                    if snapshot in TIME:
                        PI[c, p, t, a, snapshot] = 1

# === Linearizzazione ===
ATH = [(i, j, t, h) for (i, j) in model.A for t in TIME for h in H.get((i, j), [])]
model.ATH = Set(dimen=4, initialize=ATH)
model.H = Set(model.A, initialize=H)

model.b_prev = Param(model.ATH, initialize=lambda m, i, j, t, h: breakpoints[(i, j), h][0])
model.b      = Param(model.ATH, initialize=lambda m, i, j, t, h: breakpoints[(i, j), h][1])
model.tti_h  = Param(model.ATH, initialize=lambda m, i, j, t, h: tti_values[(i, j), h][1])
model.tti_h_prev = Param(model.ATH, initialize=lambda m, i, j, t, h: tti_values[(i, j), h][0])

# === Variabili ===
model.y = Var(model.CTP, domain=NonNegativeReals)
model.x = Var(model.A * model.T, domain=NonNegativeReals)
model.lmbda = Var(model.ATH, domain=NonNegativeReals)
model.eta = Var(model.A * model.T, domain=NonNegativeReals)

# === Vincoli ===
def demand_rule(m, c):
    return sum(m.y[c, p, tau] for (c2, p, tau) in m.CTP if c2 == c) == m.dem[c]
model.demand_satisfied = Constraint(model.C, rule=demand_rule)

def flow_rule(m, i, j, t):
    z_val = m.Z[i, j, t] if (i, j, t) in m.Z else 0
    return m.x[i, j, t] == z_val + sum(
        PI[c, p, tau, (i, j), t] * m.y[c, p, tau]
        for (c, p, tau) in m.CTP if (c, p, tau, (i, j), t) in PI
    )
model.flow_def = Constraint(model.A * model.T, rule=flow_rule)

def lambda_sum_rule(m, i, j, t):
    return m.x[i, j, t] == sum(m.lmbda[i, j, t, h] for h in H.get((i, j), []))
model.lambda_sum = Constraint(model.A * model.T, rule=lambda_sum_rule)

def eta_def_rule(m, i, j, t):
    return m.eta[i, j, t] == sum(
        ((m.tti_h[i, j, t, h] - m.tti_h_prev[i, j, t, h]) /
         (m.b[i, j, t, h] - m.b_prev[i, j, t, h])) * m.lmbda[i, j, t, h]
        for h in m.H[i, j]
    )
model.eta_def = Constraint(model.A * model.T, rule=eta_def_rule)

def enforce_lambda_if_flow(m, i, j, t, h):
    return m.lmbda[i, j, t, h] <= m.x[i, j, t]
model.lambda_bound = Constraint(model.ATH, rule=enforce_lambda_if_flow)

print("✅ Settato MAX_cap_multiplier a 4!")
MAX_CAP_MULTIPLIER = 4  # Definito in alto

# Modifica il caricamento di Z
Z = {}
for (key, val) in traffic_data.items():
    i, j = key.split(",")
    a = (i, j)
    capacity_a = CAPACITY[a]
    max_allowed = MAX_CAP_MULTIPLIER * capacity_a
    for t_str, flow_val in val.items():
        t = int(t_str)
        # Applica il capping al traffico di fondo
        capped_flow = min(float(flow_val), max_allowed)
        Z[(i, j, t)] = capped_flow

def capacity_limit_rule(m, i, j, t):
    return m.x[i, j, t] <= MAX_CAP_MULTIPLIER * m.mu[i, j]

model.capacity_limit = Constraint(model.A * model.T, rule=capacity_limit_rule)


# === Funzione obiettivo ===
epsilon = 0.0001
model.obj = Objective(
    expr=sum(model.eta[i, j, t] for (i, j) in model.A for t in model.T)
         + epsilon * sum(model.eta[i, j, t] for (i, j) in model.A for t in model.T),
    sense=minimize
)
