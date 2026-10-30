import numpy as np
import pandas as pd

def haversine_km(lat1, lon1, lat2, lon2):
    r=6371
    p1,p2=np.radians(lat1),np.radians(lat2)
    dp=np.radians(lat2-lat1); dl=np.radians(lon2-lon1)
    a=np.sin(dp/2)**2+np.cos(p1)*np.cos(p2)*np.sin(dl/2)**2
    return 2*r*np.arcsin(np.sqrt(a))

def build_route_summary(allocations, snapshot, fleet):
    rows=[]
    for _,z in allocations.iterrows():
        if int(z.vehicles_assigned)==0: continue
        # Demo depot: central Chennai approximate coordinates.
        distance=haversine_km(13.0569,80.2425,z.lat,z.lon)
        speed=28*(1-z.traffic_index/150)
        minutes=distance/max(speed,8)*60 + 8
        rows.append({"zone_name":z.zone_name,"vehicle_ids":z.vehicle_ids,
                     "vehicles":int(z.vehicles_assigned),"orders":int(z.assigned_orders),
                     "one_way_distance_km":round(float(distance),1),
                     "estimated_travel_minutes":round(float(minutes),1),
                     "congestion":z.congestion})
    return pd.DataFrame(rows)
