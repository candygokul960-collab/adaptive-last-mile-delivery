import numpy as np
import pandas as pd

def _greedy_allocate(zones, vehicles, objective):
    zones = zones.copy()
    zones["vehicles_assigned"] = 0
    zones["assigned_orders"] = 0
    zones["unserved_orders"] = zones["predicted_orders"].astype(int)
    available = len(vehicles)
    while available > 0:
        candidates = zones[zones.unserved_orders > 0].copy()
        if candidates.empty:
            break
        if objective == "Minimize late deliveries":
            candidates["score"] = candidates.unserved_orders * (1 + candidates.traffic_index / 100)
        elif objective == "Minimize operating cost":
            candidates["score"] = candidates.unserved_orders / (1 + candidates.traffic_index / 130)
        else:
            candidates["score"] = candidates.unserved_orders * (1 + candidates.traffic_index / 180)
        idx = candidates["score"].idxmax()
        cap = int(zones.loc[idx, "capacity_per_vehicle"])
        add = min(cap, int(zones.loc[idx, "unserved_orders"]))
        zones.loc[idx, "vehicles_assigned"] += 1
        zones.loc[idx, "assigned_orders"] += add
        zones.loc[idx, "unserved_orders"] -= add
        available -= 1
    return zones

def allocate_fleet(predictions, fleet, objective="Balanced"):
    zones = predictions.copy().reset_index(drop=True)
    vehicles = fleet.copy().reset_index(drop=True)
    zones["service_factor"] = np.clip(1.08 - zones["traffic_index"] / 180, .48, .98)
    zones["capacity_per_vehicle"] = np.maximum(
        1, np.floor(vehicles["capacity"].median() * zones["service_factor"])
    ).astype(int)

    solver_name = "OR-Tools CP-SAT"
    notes = "Integer assignment: each vehicle serves at most one zone; capacity is traffic-adjusted."
    try:
        from ortools.sat.python import cp_model
        model = cp_model.CpModel()
        x = {}
        unmet = {}
        for i, zone in zones.iterrows():
            unmet[i] = model.NewIntVar(0, int(zone.predicted_orders), f"unmet_{i}")
            assigned_capacity = []
            for j, vehicle in vehicles.iterrows():
                x[i, j] = model.NewBoolVar(f"vehicle_{j}_zone_{i}")
                traffic_factor = max(.48, min(.98, 1.08 - float(zone.traffic_index) / 180))
                cap = max(1, int(np.floor(float(vehicle.capacity) * traffic_factor)))
                assigned_capacity.append(cap * x[i, j])
            model.Add(sum(assigned_capacity) + unmet[i] >= int(zone.predicted_orders))
            model.Add(sum(assigned_capacity) <= int(zone.predicted_orders) + sum(
                max(1, int(np.floor(float(v.capacity) * max(.48, min(.98, 1.08-float(zone.traffic_index)/180)))))
                * x[i, j] for j, v in vehicles.iterrows()
            ))
        for j in range(len(vehicles)):
            model.Add(sum(x[i, j] for i in range(len(zones))) <= 1)

        # Unserved parcels dominate the objective; secondary terms favor lower
        # traffic exposure and lower operating-cost vehicle types.
        objective_terms = []
        for i, zone in zones.iterrows():
            objective_terms.append(10000 * unmet[i])
            for j, vehicle in vehicles.iterrows():
                traffic_penalty = int(zone.traffic_index * 2)
                cost_penalty = int(float(vehicle.cost_factor) * 10)
                if objective == "Minimize late deliveries":
                    traffic_penalty *= 4
                elif objective == "Minimize operating cost":
                    cost_penalty *= 5
                objective_terms.append((traffic_penalty + cost_penalty) * x[i, j])
        model.Minimize(sum(objective_terms))
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 3.0
        solver.parameters.num_search_workers = 8
        status = solver.Solve(model)
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            raise RuntimeError("CP-SAT did not find a feasible allocation")
        zones["vehicles_assigned"] = 0
        zones["assigned_orders"] = 0
        zones["unserved_orders"] = 0
        zones["vehicle_ids"] = ""
        for i, zone in zones.iterrows():
            selected = []
            cap_total = 0
            for j, vehicle in vehicles.iterrows():
                if solver.Value(x[i, j]):
                    selected.append(str(vehicle.vehicle_id))
                    factor = max(.48, min(.98, 1.08 - float(zone.traffic_index) / 180))
                    cap_total += max(1, int(np.floor(float(vehicle.capacity) * factor)))
            covered = min(int(zone.predicted_orders), cap_total)
            zones.loc[i, "vehicles_assigned"] = len(selected)
            zones.loc[i, "assigned_orders"] = covered
            zones.loc[i, "unserved_orders"] = int(zone.predicted_orders) - covered
            zones.loc[i, "vehicle_ids"] = ", ".join(selected)
    except Exception as exc:
        zones = _greedy_allocate(zones, vehicles, objective)
        solver_name = "Greedy fallback (OR-Tools unavailable or timed out)"
        notes = f"Fallback allocator used: {type(exc).__name__}. Install ortools to enable CP-SAT."

    zones["late_risk_pct"] = np.clip(
        8 + zones["traffic_index"] * .48 +
        (zones["predicted_orders"] - zones["assigned_orders"]).clip(lower=0) * .35, 5, 95
    ).round(1)
    zones["allocation_reason"] = zones.apply(
        lambda r: f"{int(r.vehicles_assigned)} vehicle(s); {r.congestion.lower()} congestion; "
                  f"{int(r.assigned_orders)} orders covered", axis=1
    )
    if "vehicle_ids" not in zones:
        zones["vehicle_ids"] = ""
        remaining = list(vehicles["vehicle_id"])
        for i in zones.sort_values("vehicles_assigned", ascending=False).index:
            n = int(zones.loc[i, "vehicles_assigned"])
            zones.loc[i, "vehicle_ids"] = ", ".join(remaining[:n])
            del remaining[:n]
    meta = {"solver": solver_name, "objective": objective, "notes": notes}
    return zones, meta
