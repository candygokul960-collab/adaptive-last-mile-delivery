# Adaptive Last-Mile Delivery Fleet Allocation

A Streamlit prototype that forecasts delivery demand by zone, simulates traffic, allocates a constrained fleet and estimates traffic-adjusted delivery travel times.

## Features
- Dashboard KPIs for demand, coverage, vehicles deployed, traffic and late risk.
- Interactive Chennai demo map with zone demand and congestion.
- Random Forest demand forecast trained on generated sample data.
- Capacity-aware adaptive fleet allocation with three objective modes.
- Haversine-based depot-to-zone travel-time estimate.
- CSV-ready modular structure for replacing synthetic data with real feeds.

## 1. Run locally

Python 3.10 or newer is recommended.

```bash
# Windows PowerShell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## 2. Project structure

```text
adaptive_last_mile_delivery/
├── app.py
├── requirements.txt
├── .env.example
├── README.md
├── .streamlit/config.toml
└── src/
    ├── __init__.py
    ├── data.py
    ├── demand_model.py
    ├── optimizer.py
    └── routing.py
```

## 3. How it works

1. `data.py` supplies demo zones, fleet and simulated order/traffic snapshots.
2. `demand_model.py` trains a Random Forest regressor and forecasts zone-level orders.
3. `optimizer.py` allocates the finite fleet to zones with unmet demand, adjusting service capacity for congestion.
4. `routing.py` estimates depot-to-zone travel time using straight-line distance and traffic-adjusted speed.
5. `app.py` renders the dashboard, map, allocation table and analytics.

## 4. Live data integration roadmap

The initial project intentionally runs with simulated data. To connect real services:

- **Traffic:** TomTom Traffic Flow API or Google Routes API. Keep API keys in environment variables; never commit secrets.
- **Routing:** Google Routes API, HERE Routing or OSRM for road-network distance and duration.
- **Weather:** OpenWeatherMap can provide rain/weather features that affect travel speed and demand.
- **Orders:** connect an order-management database/API and aggregate order timestamps by zone and time window.
- **Fleet GPS:** consume driver/vehicle location pings and update vehicle availability.

Create a `.env` file from `.env.example` and add credentials. Implement provider calls in a separate `src/integrations/` module with timeouts, retries, caching and rate-limit handling.

## 5. Important modelling notes

- The generated training set is only for demonstrating the ML workflow. Its metrics are not evidence of real-world predictive performance.
- Replace synthetic training data with at least several weeks of timestamped historical orders, zone identifiers, promotions, weather and calendar features.
- Validate using a chronological train/test split to avoid future-data leakage.
- The allocation uses OR-Tools CP-SAT when available to assign each vehicle to at most one zone while minimizing unserved demand with traffic and operating-cost penalties. A greedy fallback keeps the demo runnable if OR-Tools is unavailable. This is zone-level fleet assignment, not yet a full Vehicle Routing Problem with Time Windows (VRPTW). For production, extend it with depot, service times, time windows, driver shifts and road travel-time matrices.
- The current travel-time values are illustrative estimates from straight-line distance, not turn-by-turn road routes.
- Late risk is a heuristic signal, not a calibrated probability.

## 6. Deployment

### Streamlit Community Cloud
1. Push the project folder to a GitHub repository.
2. In Streamlit Community Cloud, create an app from that repository.
3. Set the main file path to `app.py`.
4. Add optional API credentials under app Secrets (not in source code).
5. Deploy.

## Suggested academic project title
**Adaptive Last-Mile Delivery Fleet Allocation Using Live Traffic and Demand Signals**

### Suggested objectives
- Forecast short-term delivery demand at zone level.
- Model traffic congestion as a dynamic operational constraint.
- Allocate a limited fleet to minimize unserved demand and delivery delay.
- Estimate route travel time and evaluate fleet utilization.
- Compare fixed allocation against adaptive allocation under varying demand and traffic.


## Included submission materials

- `ABSTRACT.md` — project abstract.
- `Adaptive_Last_Mile_Delivery_Presentation.pptx` — project presentation.
- `app.py` — Streamlit dashboard entry point (includes the corrected traffic-column merge).

## Run the project on Windows PowerShell

From the project folder:

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m streamlit run app.py
```

Then open `http://localhost:8501` in a browser.

The application uses simulated data by default. Do not describe the demo as using live traffic APIs unless those integrations have been implemented and configured.


## 7. Streamlit deployment and downloads

The dashboard includes a **Project Downloads** tab with downloads for:
- Abstract in Word format (`.docx`) and Markdown (`.md`).
- Project presentation (`.pptx`).
- Complete source code (`.zip`).

For GitHub and Streamlit Community Cloud deployment, follow `DEPLOYMENT_GUIDE.md`.
Set the Streamlit main file path to `app.py`.

The demo runs on synthetic data and does not require API credentials. Live traffic and routing integrations are future work.
