import json
from pyomo.environ import *
from collections import defaultdict

# === Caricamento dati ===
with open("dati/nodes_test.json") as f:
    nodes_data = json.load(f)["nodes"]
with open("dati/arcs_test.json") as f:
    arcs_data = json.load(f)["edges"]
with open("dati/trips_test.json") as f:
    trips_data = json.load(f)["trips"]
with open("dati/traffic_test.json") as f:
    traffic_data = json.load(f)["traffic"]
with open("dati/linearization_test.json") as f:
    lin_data = json.load(f)
with open("dati/c_cost.json") as f:
    c_cost_data = json.load(f)
with open("dati/c_cost_FP.json") as f:
    c_cost_FF = json.load(f)

print("\n✅ Dati caricati!")

# === Set base ===
NODES = [n["id"] for n in nodes_data]
ARCS = [(a["from"], a["to"]) for a in arcs_data]
TIME = list(range(1, 50))
TRIPS = list(range(len(trips_data)))
PATHS_PER_TRIP = {c: list(range(len(trips_data[c]["paths"]))) for c in TRIPS}

print("\n✅ Set base caricato!")

# === Parametri arc ===
FFTT = {(a["from"], a["to"]): a["fftt"] for a in arcs_data}
CAPACITY = {(a["from"], a["to"]): a["capacity"] for a in arcs_data}
Z = {(row["from"], row["to"], row["time"]): row["forecast"] for row in traffic_data}

print("\n✅ Parametri arc caricati!")

# === Parametri linearizzazione ===
breakpoints = {}
tti_values = {}
H = {}
for key, val in lin_data.items():
    i, j = key.split("_")
    a = (i, j)
    bp = val["breakpoints"]
    tti = val["tti_values"]
    H[a] = list(range(1, len(bp)))
    for h in H[a]:
        breakpoints[a, h] = (bp[h-1], bp[h])
        tti_values[a, h] = (tti[h-1], tti[h])

print("\n✅ Parametri linearizzazione caricati!")

# === Pyomo model ===
model = ConcreteModel()
model.A = Set(initialize=ARCS, dimen=2)
model.T = Set(initialize=TIME)
model.C = Set(initialize=TRIPS)
model.PATHS = Set(model.C, initialize=PATHS_PER_TRIP)

print("\n✅ Pyomo sets caricati!")

# === Parametri dei trip ===
DEMAND = {c: trips_data[c]["demand"] for c in TRIPS}
model.dem = Param(model.C, initialize=DEMAND)
model.fftt = Param(model.A, initialize=FFTT)
model.mu = Param(model.A, initialize=CAPACITY)
model.Z = Param(model.A * model.T, initialize=Z, default=0)

print("\n✅ Parametri trip caricati!")

# === Preferenze di partenza ===
# Estraggo il tempo preferito per ogni trip
PREF = {c: int(trips_data[c]["departure_times"][0]) for c in TRIPS}
# Costruisco un dizionario is_pref[(c,p,tau)] = 1 se tau == PREF[c], altrimenti 0
is_pref = {}
ctp_list = []
for c in TRIPS:
    for p, path in enumerate(trips_data[c]["paths"]):
        for tau in path["possible_departure_times"]:
            t_int = int(tau)
            key = (c, p, t_int)
            if f"{c}_{p}_{t_int}" in c_cost_data:
                ctp_list.append((c, p, t_int))
                is_pref[c, p, t_int] = 1 if t_int == PREF[c] else 0

model.CTP = Set(initialize=ctp_list, dimen=3)
model.is_pref = Param(model.CTP, initialize=is_pref, within=Binary)

print("\n✅ CTP e preferenze caricate!")

# === π_cpτ^{at} ===
PI = defaultdict(int)
for c in TRIPS:
    for p, path in enumerate(trips_data[c]["paths"]):
        arcs = [(a[0], a[1]) for a in path["arcs"]]
        fftts = path["base_times"]
        for tau in path["possible_departure_times"]:
            t = int(tau)
            if f"{c}_{p}_{t}" not in c_cost_data:
                continue
            for (a, tt) in zip(arcs, fftts):
                for offset in range(tt):
                    snapshot = t + offset
                    if snapshot in TIME:
                        PI[c, p, t, a, snapshot] = 1

print("\n✅ π_cpt caricati!")

# === Parametri linearizzazione Pyomo ===
ATH = []
for (i, j) in model.A:
    for t in TIME:
        for h in H.get((i, j), []):
            ATH.append((i, j, t, h))

model.ATH = Set(dimen=4, initialize=ATH)
model.H = Set(model.A, initialize=H)
model.lmbda = Var(model.ATH, domain=NonNegativeReals)

model.b_prev = Param(model.ATH, initialize=lambda m, i, j, t, h: breakpoints[(i, j), h][0])
model.b      = Param(model.ATH, initialize=lambda m, i, j, t, h: breakpoints[(i, j), h][1])
model.tti_h  = Param(model.ATH, initialize=lambda m, i, j, t, h: tti_values[(i, j), h][1])
model.tti_h_prev = Param(model.ATH, initialize=lambda m, i, j, t, h: tti_values[(i, j), h][0])

print("\n✅ Parametri linearizzazione Pyomo caricati!")

# === Variabili ===
model.y = Var(model.CTP, domain=NonNegativeReals)
model.x = Var(model.A * model.T, domain=NonNegativeReals)
model.sigma = Var(model.A * model.T, domain=NonNegativeReals)

# === Costi ===
# Costo di viaggio reale per ogni (c,p,τ)
COST = {(int(k.split("_")[0]), int(k.split("_")[1]), int(k.split("_")[2])): v
        for k, v in c_cost_data.items()}
# Costo di free-flow per ogni trip c
COST_FF = {int(k): v for k, v in c_cost_FF.items()}

model.fftt_c = Param(model.C, initialize=COST_FF, default=1)
model.c_cost = Param(model.CTP, initialize=COST, default=999999)

print("\n✅ Parametri costo caricati!")

# === Vincoli ===

def demand_rule(m, c):
    return sum(m.y[c, p, tau] for (c2, p, tau) in m.CTP if c2 == c) == m.dem[c]
model.demand_satisfied = Constraint(model.C, rule=demand_rule)

def flow_rule(m, i, j, t):
    return m.x[i, j, t] == m.Z[i, j, t] + sum(
        PI[c, p, tau, (i, j), t] * m.y[c, p, tau]
        for (c, p, tau) in m.CTP if (c, p, tau, (i, j), t) in PI
    )
model.flow_def = Constraint(model.A * model.T, rule=flow_rule)

def lambda_sum_rule(m, i, j, t):
    return m.x[i, j, t] == sum(m.lmbda[i, j, t, h] for h in H.get((i, j), []))
model.lambda_sum = Constraint(model.A * model.T, rule=lambda_sum_rule)

def sigma_def_rule(m, i, j, t):
    return m.sigma[i, j, t] == 1 + sum(
        ((m.tti_h[i, j, t, h] - m.tti_h_prev[i, j, t, h]) /
         (m.b[i, j, t, h] - m.b_prev[i, j, t, h])) * m.lmbda[i, j, t, h]
        for h in m.H[i, j]
    )
model.sigma_def = Constraint(model.A * model.T, rule=sigma_def_rule)

def enforce_lambda_if_flow(m, i, j, t, h):
    return m.lmbda[i, j, t, h] <= m.x[i, j, t]
model.lambda_bound = Constraint(model.ATH, rule=enforce_lambda_if_flow)

def arc_capacity_rule(m, i, j, t):
    return m.x[i, j, t] <= 4 * m.mu[i, j]
model.arc_capacity = Constraint(model.A * model.T, rule=arc_capacity_rule)

def time_distribution_rule(m, t):
    max_vehicles_per_time = sum(m.dem[c] for c in m.C) * 0.3
    return sum(m.y[c, p, tau] for (c, p, tau) in m.CTP if tau == t) <= max_vehicles_per_time
model.time_distribution = Constraint(model.T, rule=time_distribution_rule)

ALPHA = 2.0
def tti_bound_rule(m, i, j, t):
    return m.sigma[i, j, t] <= ALPHA
model.tti_bound = Constraint(model.A * model.T, rule=tti_bound_rule)

print("\n✅ Vincoli caricati!")

# === Funzione obiettivo ===
epsilon = 0.0001
beta = 1.0  # peso del termine di preferenza
# Somma dei costi di viaggio + epsilon * SUM(sigma) + beta * penalità per deviation dalla preferenza
def obj_rule(m):
    travel_cost = sum(
        (m.c_cost[c, p, tau] / m.fftt_c[c]) * m.y[c, p, tau]
        for (c, p, tau) in m.CTP
    )
    penalty_pref = beta * sum(
        (1 - m.is_pref[c, p, tau]) * m.y[c, p, tau] for (c, p, tau) in m.CTP
    )
    tti_term = epsilon * sum(m.sigma[i, j, t] for (i, j) in m.A for t in m.T)
    return travel_cost + tti_term + penalty_pref

model.obj = Objective(rule=obj_rule, sense=minimize)

print("\n✅ Funzione obiettivo con preferenze creata!")
