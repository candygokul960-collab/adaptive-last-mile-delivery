import numpy as np
import pandas as pd

def load_demo_data():
    zones = pd.DataFrame([
        ("Z01","T. Nagar",13.0418,80.2337,42,0.9),
        ("Z02","Adyar",13.0012,80.2565,35,0.8),
        ("Z03","Velachery",12.9750,80.2210,55,1.2),
        ("Z04","Anna Nagar",13.0850,80.2101,38,0.9),
        ("Z05","Mylapore",13.0368,80.2676,31,0.8),
        ("Z06","Porur",13.0358,80.1560,47,1.0),
        ("Z07","Tambaram",12.9249,80.1000,60,1.3),
        ("Z08","OMR",12.9165,80.2295,52,1.2),
        ("Z09","Ambattur",13.1143,80.1548,34,0.9),
        ("Z10","Perungudi",12.9600,80.2460,45,1.1),
    ], columns=["zone_id","zone_name","lat","lon","historical_avg_orders","demand_weight"])
    fleet = pd.DataFrame([
        ("V01","Bike",18,42,1.0),("V02","Bike",18,38,1.0),("V03","Bike",18,40,1.0),
        ("V04","Bike",18,36,1.0),("V05","Bike",18,35,1.0),("V06","Bike",18,41,1.0),
        ("V07","Van",45,34,1.15),("V08","Van",45,37,1.15),("V09","Van",45,32,1.15),
        ("V10","EV Van",38,39,1.05),("V11","EV Van",38,35,1.05),("V12","EV Van",38,40,1.05),
    ], columns=["vehicle_id","vehicle_type","capacity","avg_speed_kmph","cost_factor"])
    orders = pd.DataFrame(columns=["order_id","zone_id","created_at","status"])
    return orders, fleet, zones

def make_live_snapshot(orders, zones, demand_scale=1.0, traffic_scale=1.0, seed=None):
    rng = np.random.default_rng(seed)
    out = zones.copy()
    hour = 17
    peak = 1.25 if hour in [8,9,17,18,19] else 1.0
    out["historical_avg_orders"] = out["historical_avg_orders"].astype(float)
    out["observed_orders"] = np.maximum(1, rng.poisson(out["historical_avg_orders"] * demand_scale * peak))
    out["traffic_index"] = np.clip(rng.normal(45, 17, len(out)) * traffic_scale + (out["observed_orders"]/out["historical_avg_orders"]-1)*18, 8, 98).round().astype(int)
    out["congestion"] = pd.cut(out["traffic_index"], bins=[-1,35,65,101], labels=["Low","Medium","High"]).astype(str)
    out["hour"] = hour
    out["weekday"] = 4
    return out
