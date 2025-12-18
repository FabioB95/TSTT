import json
from collections import defaultdict

def debug_model_data():
   
    print("🔍 ANALISI FEASIBILITY DEI DATI")
    print("=" * 50)
    
    # Carica dati
    with open("dati/trips_test.json") as f:
        trips_data = json.load(f)["trips"]
    with open("dati/arcs_test.json") as f:
        arcs_data = json.load(f)["edges"]
    with open("dati/c_cost.json") as f:
        c_cost_data = json.load(f)
    
    ARCS = [(a["from"], a["to"]) for a in arcs_data]
    CAPACITY = {(a["from"], a["to"]): a["capacity"] for a in arcs_data}
    
    print(f"📊 STATISTICHE GENERALI:")
    print(f"- Numero trips: {len(trips_data)}")
    print(f"- Numero archi: {len(ARCS)}")
    print(f"- Combinazioni c_cost: {len(c_cost_data)}")
    
    # 1. Analizza ogni trip
    total_demand = 0
    trips_without_options = []
    
    for c, trip in enumerate(trips_data):
        demand = trip["demand"]
        total_demand += demand
        
        # Conta opzioni valide per questo trip
        valid_options = 0
        for p, path in enumerate(trip["paths"]):
            for tau in path["possible_departure_times"]:
                key = f"{c}_{p}_{int(tau)}"
                if key in c_cost_data:
                    valid_options += 1
        
        if valid_options == 0:
            trips_without_options.append(c)
            print(f"❌ Trip {c}: demand={demand}, opzioni=0")
        else:
            print(f"✅ Trip {c}: demand={demand}, opzioni={valid_options}")
    
    print(f"\n📈 DOMANDA TOTALE: {total_demand}")
    
    if trips_without_options:
        print(f"\n❌ TRIPS SENZA OPZIONI: {trips_without_options}")
        return False
    
    # 2. Analizza capacità vs domanda
    print(f"\n🛣️ ANALISI CAPACITÀ:")
    capacities = list(CAPACITY.values())
    print(f"- Capacità minima: {min(capacities)}")
    print(f"- Capacità massima: {max(capacities)}")
    print(f"- Capacità media: {sum(capacities)/len(capacities):.1f}")
    
    # Stima capacità totale della rete (approssimativa)
    total_network_capacity = sum(capacities) * 10  # Assumendo utilizzo su 10 time slots
    print(f"- Capacità rete stimata: {total_network_capacity}")
    
    if total_demand > total_network_capacity:
        print(f"⚠️ DOMANDA > CAPACITÀ RETE!")
        return False
    
    # 3. Analizza percorsi
    print(f"\n🗺️ ANALISI PERCORSI:")
    missing_arcs = set()
    valid_paths = 0
    invalid_paths = 0
    
    for c, trip in enumerate(trips_data):
        for p, path in enumerate(trip["paths"]):
            path_valid = True
            for arc in path["arcs"]:
                arc_tuple = (arc[0], arc[1])
                if arc_tuple not in CAPACITY:
                    missing_arcs.add(arc_tuple)
                    path_valid = False
            
            if path_valid:
                valid_paths += 1
            else:
                invalid_paths += 1
    
    print(f"- Percorsi validi: {valid_paths}")
    print(f"- Percorsi invalidi: {invalid_paths}")
    
    if missing_arcs:
        print(f"❌ ARCHI MANCANTI: {list(missing_arcs)[:5]}...")  # Mostra primi 5
        return False
    
    # 4. Analizza distribuzione costi
    costs = list(c_cost_data.values())
    print(f"\n💰 ANALISI COSTI:")
    print(f"- Costo minimo: {min(costs):.2f}")
    print(f"- Costo massimo: {max(costs):.2f}")
    print(f"- Costo medio: {sum(costs)/len(costs):.2f}")
    
    # 5. Raccomandazioni
    print(f"\n💡 RACCOMANDAZIONI:")
    
    if min(capacities) < max(trip["demand"] for trip in trips_data):
        print("⚠️ Alcune capacità archi sono inferiori alla domanda max di singoli trip")
        print("   Considera di aumentare le capacità o ridurre la domanda")
    
    if len(c_cost_data) < 100:
        print("⚠️ Poche combinazioni c_cost disponibili")
        print("   Considera di espandere possible_departure_times o ridurre max_delay")
    
    print("\n✅ ANALISI COMPLETATA")
    return True

def suggest_fixes():
    
    print("\n🔧 SUGGERIMENTI DI CORREZIONE:")
    print("=" * 50)
    
    print("1. Se hai trips senza opzioni:")
    print("   - Aumenta max_delay in generate_cost.py")
    print("   - Aggiungi più possible_departure_times nei dati")
    print("   - Riduci la penalità delay_weight")
    
    print("\n2. Se hai problemi di capacità:")
    print("   - Aumenta le capacità degli archi critici")
    print("   - Riduci la domanda di alcuni trip")
    print("   - Aumenta il numero di time slots")
    
    print("\n3. Se hai problemi di linearizzazione:")
    print("   - Controlla che tutti gli archi abbiano dati in linearization_test.json")
    print("   - Aumenta ALPHA nel modello (da 2.0 a 5.0 o più)")
    
    print("\n4. Modifiche al modello:")
    print("   - Usa il modello corretto che ho fornito")
    print("   - Riduci epsilon per dare più peso ai costi di viaggio")
    print("   - Aggiungi vincoli soft se necessario")

if __name__ == "__main__":
    is_feasible = debug_model_data()
    suggest_fixes()
    
    if not is_feasible:
        print("\n❌ MODELLO PROBABILMENTE INFEASIBLE")
        print("Applica le correzioni suggerite prima di eseguire l'ottimizzazione")
    else:
        print("\n✅ DATI SEMBRANO FEASIBLE")
        print("Usa il modello corretto per l'ottimizzazione")