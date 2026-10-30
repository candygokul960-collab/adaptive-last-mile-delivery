import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

def synthetic_training_data(seed=21, n=1800):
    rng = np.random.default_rng(seed)
    zone = rng.integers(0,10,n)
    hour = rng.integers(0,24,n)
    weekday = rng.integers(0,7,n)
    historical = rng.choice([31,34,35,38,42,45,47,52,55,60],n)
    traffic = rng.integers(5,100,n)
    weekend = (weekday >= 5).astype(int)
    rush = np.isin(hour,[8,9,17,18,19]).astype(int)
    lunch = np.isin(hour,[12,13,14]).astype(int)
    noise = rng.normal(0,5,n)
    demand = historical*(0.62 + .22*rush + .10*lunch + .08*weekend) + .08*traffic + noise
    demand = np.maximum(2,demand)
    return pd.DataFrame({"zone_code":zone,"hour":hour,"weekday":weekday,"historical_avg_orders":historical,
                         "traffic_index":traffic,"weekend":weekend,"rush_hour":rush}), demand

def train_demand_model():
    X,y = synthetic_training_data()
    X_train,X_test,y_train,y_test = train_test_split(X,y,test_size=.22,random_state=7)
    model = RandomForestRegressor(n_estimators=160,max_depth=12,min_samples_leaf=2,random_state=7,n_jobs=-1)
    model.fit(X_train,y_train)
    pred = model.predict(X_test)
    return model, {"mae":mean_absolute_error(y_test,pred),"r2":r2_score(y_test,pred)}

def predict_zone_demand(model, snapshot, horizon="Next 4 hours"):
    horizon_hours = {"Next 2 hours":2,"Next 4 hours":4,"Next 8 hours":8}[horizon]
    x = snapshot.copy()
    x["zone_code"] = np.arange(len(x))
    x["weekend"] = (x["weekday"]>=5).astype(int)
    x["rush_hour"] = x["hour"].isin([8,9,17,18,19]).astype(int)
    features = x[["zone_code","hour","weekday","historical_avg_orders","traffic_index","weekend","rush_hour"]]
    # Scale the model's one-hour estimate to the requested planning horizon.
    x["predicted_orders"] = np.maximum(1, np.rint(model.predict(features) * horizon_hours / 4))
    x["demand_level"] = pd.cut(x["predicted_orders"], bins=[-1,30,55,10000], labels=["Low","Medium","High"]).astype(str)
    return x[["zone_id","zone_name","lat","lon","historical_avg_orders","traffic_index","congestion","predicted_orders","demand_level"]]
