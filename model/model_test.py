
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

print("\n✅Dati caricati!")

# === Set base ===
NODES = [n["id"] for n in nodes_data]
ARCS = [(a["from"], a["to"]) for a in arcs_data]
TIME = list(range(1, 108))
TRIPS = list(range(len(trips_data)))
PATHS_PER_TRIP = {c: list(range(len(trips_data[c]["paths"]))) for c in TRIPS}
#COSTS_FP = {c_cost_FF: list(range(len(c_cost_FF[c])))for c in TRIPS}

print("\n✅Set base caricato!")

# === Parametri arc ===
FFTT = {(a["from"], a["to"]): a["fftt"] for a in arcs_data}
CAPACITY = {(a["from"], a["to"]): a["capacity"] for a in arcs_data}
Z = {(row["from"], row["to"], row["time"]): row["forecast"] for row in traffic_data}

print("\n✅Parametri arc caricati!")

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


print("\n✅Parametri lienarizzazione caricati!")

# === Pyomo model ===
model = ConcreteModel()
model.A = Set(initialize=ARCS, dimen=2)
model.T = Set(initialize=TIME)
model.C = Set(initialize=TRIPS)
model.PATHS = Set(model.C, initialize=PATHS_PER_TRIP)


print("\n✅Pyomo caricati!")

# === Parametri dei trip ===
DEMAND = {c: trips_data[c]["demand"] for c in TRIPS}
model.dem = Param(model.C, initialize=DEMAND)
model.fftt = Param(model.A, initialize=FFTT)
model.mu = Param(model.A, initialize=CAPACITY)
model.Z = Param(model.A * model.T, initialize=Z, default=0)



print("\n✅Paramentri trip caricati!")

# === CTP ===
ctp_set = []
for c in TRIPS:
    for p, path in enumerate(trips_data[c]["paths"]):
        for tau in path["possible_departure_times"]:
            key = f"{c}_{p}_{int(tau)}"
            if key in c_cost_data:
                ctp_set.append((c, p, int(tau)))
model.CTP = Set(initialize=ctp_set, dimen=3)


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
                    if snapshot in TIME:
                        PI[c, p, t, a, snapshot] = 1


print("\n✅pi_cpt caricati!")

# === Parametri linearizzazione Pyomo ===

ATH = []
for (i, j) in model.A:
    for t in TIME:
        for h in H.get((i, j), []): 
            ATH.append((i, j, t, h))

model.ATH = Set(dimen=4, initialize=ATH)

model.lmbda = Var(model.ATH, domain=NonNegativeReals)

# === Parametri linearizzazione ===
model.H = Set(model.A, initialize=H)
model.b_prev = Param(model.ATH, initialize=lambda m, i, j, t, h: breakpoints[(i, j), h][0])
model.b      = Param(model.ATH, initialize=lambda m, i, j, t, h: breakpoints[(i, j), h][1])
model.tti_h  = Param(model.ATH, initialize=lambda m, i, j, t, h: tti_values[(i, j), h][1])
model.tti_h_prev = Param(model.ATH, initialize=lambda m, i, j, t, h: tti_values[(i, j), h][0])


# === Variabili ===
model.y = Var(model.CTP, domain=NonNegativeReals)
model.x = Var(model.A * model.T, domain=NonNegativeReals)
model.sigma = Var(model.A * model.T, domain=NonNegativeReals)

# === Costi ===
COST = {(int(k.split("_")[0]), int(k.split("_")[1]), int(k.split("_")[2])): v for k, v in c_cost_data.items()}
COST_FF = {(int(k)): v for k,v in c_cost_FF.items()}
model.fftt_c = Param(model.C, initialize = COST_FF, default = 1)
model.c_cost = Param(model.CTP, initialize=COST, default=999999)


print("\n✅Paraemntri, costi, variabili caricati!")

# === Vincoli ===

def demand_rule(m, c):
    return sum(m.y[c, p, tau] for (c2, p, tau) in m.CTP if c2 == c) == m.dem[c]
model.demand_satisfied = Constraint(model.C, rule=demand_rule)

print("\n✅Demand_rule")

def flow_rule(m, i, j, t):
    return m.x[i, j, t] == m.Z[i, j, t] + sum(
        PI[c, p, tau, (i, j), t] * m.y[c, p, tau]
        for (c, p, tau) in m.CTP if (c, p, tau, (i, j), t) in PI
    )
model.flow_def = Constraint(model.A * model.T, rule=flow_rule)

print("\n✅Flow_rule")

def lambda_sum_rule(m, i, j, t):
    return m.x[i, j, t] == sum(
        m.lmbda[i, j, t, h] for h in H.get((i, j), [])
    )
model.lambda_sum = Constraint(model.A * model.T, rule=lambda_sum_rule)

print("\n✅Lambda_sum_rule")

def sigma_def_rule(m, i, j, t):
    return m.sigma[i, j, t] == 1+ sum(
        ((m.tti_h[i, j, t, h] - m.tti_h_prev[i, j, t, h]) /
         (m.b[i, j, t, h] - m.b_prev[i, j, t, h])) * m.lmbda[i, j, t, h]
        for h in m.H[i, j]
    )
model.sigma_def = Constraint(model.A * model.T, rule=sigma_def_rule)

print("\n✅Sigma_sum_rule")

def enforce_lambda_if_flow(m, i, j, t, h):
    return m.lmbda[i, j, t, h] <= m.x[i, j, t]
model.lambda_bound = Constraint(model.ATH, rule=enforce_lambda_if_flow)

print("\n✅Enforce_lambda_rule")

def arc_capacity_rule(m, i, j, t):
    return m.x[i, j, t] <= 4*m.mu[i, j]
model.arc_capacity = Constraint(model.A * model.T, rule=arc_capacity_rule)

print("\n✅Arc_capacity")


def time_distribution_rule(m, t):
   
    max_vehicles_per_time = sum(m.dem[c] for c in m.C) * 0.3 
    return sum(m.y[c, p, tau] for (c, p, tau) in m.CTP if tau == t) <= max_vehicles_per_time

model.time_distribution = Constraint(model.T, rule=time_distribution_rule)

print("\n✅Time_distribution_rule")

ALPHA = 2.0
def tti_bound_rule(m, i, j, t):
    return m.sigma[i, j, t] <= ALPHA
model.tti_bound = Constraint(model.A * model.T, rule=tti_bound_rule)


print("\n✅Vincoli  caricati!")

# === Funzione obiettivo ===
epsilon = 0.0001
model.obj = Objective(
    expr=(sum((model.c_cost[c, p, tau]/model.fftt_c[c]) * model.y[c, p, tau] for (c, p, tau) in model.CTP))
        + epsilon * sum(model.sigma[i, j, t] for (i, j) in model.A for t in model.T),
    sense=minimize
)

print("\n✅Fatto!")