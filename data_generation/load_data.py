import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from model.node import Nodo
from model.arc import Arc

def load_nodes(filepath):
    with open(filepath, 'r') as f:
        data = json.load(f)
    return [Nodo.from_dict(d) for d in data["nodes"]]

def load_arcs(filepath):
    with open(filepath, 'r') as f:
        data = json.load(f)
    return [Arc.from_dict(d) for d in data["edges"]]


if __name__ == "__main__":
    nodes = load_nodes('dati/nodes_with_indices.json')
    arcs = load_arcs('dati/arcs.json')

    print(f"Caricati {len(nodes)} nodi e {len(arcs)} archi")
