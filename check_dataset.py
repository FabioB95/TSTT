import pandas as pd
import json

# Load dataset
df_trips = pd.read_excel("dataset_low_traffic_1000.xlsx", sheet_name="trips")
df_arcs = pd.read_excel("dataset_low_traffic_1000.xlsx", sheet_name="arcs")

# Check demand
total_demand = df_trips['demand'].sum()
print(f"Total Demand: {total_demand:,.0f}")
print(f"Number of trips: {len(df_trips)}")
print(f"Avg demand per trip: {total_demand/len(df_trips):.1f}")

# Check background traffic
with open("dati/traffic_DEF_L.json", "r") as f:
    Z = json.load(f)

total_Z = sum(sum(d.values()) for d in Z.values())
print(f"\nTotal Background Traffic: {total_Z:,.0f}")
print(f"Ratio Z/Demand: {total_Z/total_demand:.2f}")

# Check capacity
total_capacity = 0
for _, row in df_arcs.iterrows():
    cap = float(str(row['capacity']).replace(',', '.'))
    total_capacity += cap / 4.0  # per 15-min slot

total_capacity_all_slots = total_capacity * 108  # 108 time slots
print(f"\nTotal Network Capacity (all slots): {total_capacity_all_slots:,.0f}")
print(f"Demand as % of capacity: {100*(total_demand + total_Z)/total_capacity_all_slots:.1f}%")

# Check paths per trip
path_counts = []
for _, row in df_trips.iterrows():
    k = 0
    while f"path_{k}" in row and not pd.isna(row.get(f"path_{k}")):
        k += 1
    path_counts.append(k)

print(f"\nAvg paths per trip: {sum(path_counts)/len(path_counts):.1f}")
print(f"Trips with only 1 path: {sum(1 for x in path_counts if x == 1)}")
print(f"Trips with >=3 paths: {sum(1 for x in path_counts if x >= 3)}")