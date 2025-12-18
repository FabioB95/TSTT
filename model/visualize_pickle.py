import pickle

def load_pickle(name):
    with open(f"dati/{name}.pkl", "rb") as f:
        obj = pickle.load(f)
    print(f"\n{'='*20} {name.upper()} ({len(obj)} elementi) {'='*20}")
    for k, v in list(obj.items())[:5]:  # stampa solo i primi 5
        print(f"{k}: {v}")
    print("="*60)

def main():
    for name in ["nodes", "arcs", "trips", "paths", "traffic"]:
        try:
            load_pickle(name)
        except Exception as e:
            print(f"❌ Errore con {name}: {e}")

if __name__ == "__main__":
    main()
