import json

# --- NODI ---
nodes = [{"id": f"N{i}"} for i in range(1, 8)]
with open("dati/nodes_test.json", "w") as f:
    json.dump({"nodes": nodes}, f, indent=4)

# --- ARCHI ---
arcs = [
    {"from": "N1", "to": "N2", "fftt": 20, "capacity": 250},
    {"from": "N2", "to": "N3", "fftt": 22, "capacity": 250},
    {"from": "N3", "to": "N4", "fftt": 20, "capacity": 150},
    {"from": "N4", "to": "N5", "fftt": 20, "capacity": 150},
    {"from": "N4", "to": "N6", "fftt": 20, "capacity": 150},
    {"from": "N2", "to": "N4", "fftt": 20, "capacity": 150},
    {"from": "N2", "to": "N5", "fftt": 24, "capacity": 250},
    {"from": "N3", "to": "N6", "fftt": 24, "capacity": 250},
    {"from": "N5", "to": "N6", "fftt": 24, "capacity": 250},
    {"from": "N6", "to": "N7", "fftt": 20, "capacity": 250}
]
with open("dati/arcs_test.json", "w") as f:
    json.dump({"edges": arcs}, f, indent=4)

# --- PATHS ---
all_paths = [
    ["N1", "N2", "N4", "N6", "N7"],  # Path 1
    ["N1", "N2", "N3", "N6", "N7"],  # Path 2
    ["N1", "N2", "N5", "N6", "N7"]   # Path 3
]


# --- TRAFFICO (40% della capacità) per t = 1 e 2 ---
traffic = []
for arc in arcs:
    for t in [1, 2]:
        traffic.append({
            "from": arc["from"],
            "to": arc["to"],
            "time": t,
            "forecast": 0.4 * arc["capacity"]
        })

with open("dati/traffic_test.json", "w") as f:
    json.dump({"traffic": traffic}, f, indent=4)
