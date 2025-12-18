import json
from collections import defaultdict
import os

# === CONFIG ===
NODES_FILE = "dati/nodes.json"
ARCS_FILE = "dati/arcs.json"
OUTPUT_FILE = "dati/nodes_with_indices.json"

# === MAPPING PER H_i ===
H_CATEGORY = {
    "attrazione_turistica": 1.0,
    "grande_domanda": 0.7,
    "bassa_domanda": 0.4,
    "ingresso_estero": 0.6
}

# === FUNZIONE ===
def normalize(x, min_x, max_x):
    return (x - min_x) / (max_x - min_x) if max_x > min_x else 0

def main():
    # Carica nodi e archi
    with open(NODES_FILE, 'r') as f:
        nodes_data = json.load(f)["nodes"]

    with open(ARCS_FILE, 'r') as f:
        arcs_data = json.load(f)["edges"]

    # Calcola grado per ogni nodo
    grado = defaultdict(int)
    for arc in arcs_data:
        grado[arc["from_node"]] += 1
        grado[arc["to_node"]] += 1

    # Estrai popolazioni
    pop_values = [n["population"] for n in nodes_data]
    min_pop, max_pop = min(pop_values), max(pop_values)

    # Crea nuovi nodi con H_i e I_i
    new_nodes = []
    for node in nodes_data:
        node_id = node["ID"]
        pop_norm = normalize(node["population"], min_pop, max_pop)
        grado_norm = normalize(grado[node_id], min(grado.values()), max(grado.values()))
        K_i = node.get("K_i", 0)

        H_i = H_CATEGORY.get(node["category"], 0.5)
        I_i = round(0.4 * grado_norm + 0.4 * pop_norm + 0.2 * K_i, 3)

        node["H_i"] = round(H_i, 3)
        node["I_i"] = I_i
        new_nodes.append(node)

    # Salva il file nuovo
    with open(OUTPUT_FILE, 'w') as f:
        json.dump({"nodes": new_nodes}, f, indent=2)
    
    print(f"✅ File salvato come '{OUTPUT_FILE}' con H_i e I_i aggiunti.")

if __name__ == "__main__":
    main()
