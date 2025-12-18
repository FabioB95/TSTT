import pickle
import os

# === Percorso ===
pkl_path = "dati/preprocessed_data.pkl"

if not os.path.exists(pkl_path):
    print(f"❌ File non trovato: {pkl_path}")
    exit()

with open(pkl_path, "rb") as f:
    pi_at_cpτ, time_cpτ, FP_c, P_c, T_c, dem_c, mu, T, trip_ids, arcs = pickle.load(f)

print("\n📦 === Contenuto del file preprocessed_data.pkl ===")

# --- pi_at_cpτ ---
print(f"\n🔸 pi_at_cpτ: {len(pi_at_cpτ)} elementi")
sample_keys = list(pi_at_cpτ.keys())[:3]
for k in sample_keys:
    print(f"  {k} -> {pi_at_cpτ[k]}")

# --- time_cpτ ---
print(f"\n🔸 time_cpτ: {len(time_cpτ)} elementi")
for k in list(time_cpτ.keys())[:3]:
    print(f"  {k} -> {time_cpτ[k]}")

# --- FP_c ---
print(f"\n🔸 FP_c: {len(FP_c)} trip")
for k in list(FP_c.keys())[:3]:
    print(f"  {k} -> {FP_c[k]}")

# --- P_c ---
print(f"\n🔸 P_c: {len(P_c)} trip con path")
for k in list(P_c.keys())[:3]:
    print(f"  {k} -> {P_c[k]}")

# --- T_c ---
print(f"\n🔸 T_c: {len(T_c)} trip con departure_times")
for k in list(T_c.keys())[:3]:
    print(f"  {k} -> {T_c[k]}")

# --- dem_c ---
print(f"\n🔸 dem_c: {len(dem_c)} trip con domanda")
for k in list(dem_c.keys())[:3]:
    print(f"  {k} -> {dem_c[k]}")

# --- mu ---
print(f"\n🔸 mu: {len(mu)} archi con capacità")
for k in list(mu.keys())[:3]:
    print(f"  {k} -> {mu[k]}")

# --- T ---
print(f"\n🔸 T: {len(T)} istanti temporali → {T[:10]} ...")

# --- trip_ids ---
print(f"\n🔸 trip_ids: {len(trip_ids)} → {trip_ids[:10]}")

# --- arcs ---
print(f"\n🔸 arcs: {len(arcs)} archi → {arcs[:10]}")
