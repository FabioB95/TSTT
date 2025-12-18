import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from model.node import Nodo
from data_generation.load_data import load_nodes

def compute_probabilities(nodes):
    total_PK = sum(n.P * n.K for n in nodes)
    total_IH = sum(n.I * n.H for n in nodes)

    print(f"TOTAL PK: {total_PK}")
    print(f"TOTAL IH: {total_IH}")

    probabilities = []
    for n in nodes:
        p_o = (n.P * n.K) / total_PK if total_PK > 0 else 0
        p_d = (n.I * n.H) / total_IH if total_IH > 0 else 0
        print(f"Node {n.ID}: I={n.I}, H={n.H}, I*H={n.I * n.H}, p_d={p_d}")
        probabilities.append({
            "ID": n.ID,
            "origin_prob": p_o,
            "dest_prob": p_d
        })
    return probabilities

def save_probabilities(probabilities, filepath):
    with open(filepath, 'w') as f:
        json.dump(probabilities, f, indent=4)

if __name__ == "__main__":
    nodes = load_nodes("dati/nodes_with_indices.json")
    probs = compute_probabilities(nodes)
    save_probabilities(probs, "dati/nodi_prob.json")
    print("✅ Probabilità salvate in dati/nodi_prob.json")
