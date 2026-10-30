import streamlit as st
import io
import zipfile
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from streamlit_folium import st_folium
import folium

from src.data import load_demo_data, make_live_snapshot
from src.demand_model import train_demand_model, predict_zone_demand
from src.optimizer import allocate_fleet
from src.routing import build_route_summary

st.set_page_config(page_title="Adaptive Fleet Allocation", page_icon="🚚", layout="wide")
st.markdown("""
<style>
.block-container {padding-top: 1.3rem; padding-bottom: 2rem;}
[data-testid="stMetric"] {background: #1118270a; border: 1px solid #94a3b833; padding: 14px; border-radius: 12px;}
.hero {padding: 1.1rem 1.4rem; border-radius: 16px; background: linear-gradient(110deg,#102a43,#1d4e89); color: white; margin-bottom: 1rem;}
.hero p {color:#dbeafe; margin-bottom:0;}
.small-muted {color:#64748b; font-size:.88rem;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>🚚 Adaptive Last-Mile Delivery Fleet Allocation</h1><p>Allocate vehicles intelligently using demand signals, traffic conditions and fleet capacity.</p></div>', unsafe_allow_html=True)

orders, fleet, zones = load_demo_data()
model, metrics = train_demand_model()

with st.sidebar:
    st.header("Control Center")
    st.caption("Demo mode · synthetic data")
    refresh = st.button("↻ Simulate new demand & traffic", use_container_width=True)
    demand_scale = st.slider("Demand intensity", 0.6, 1.6, 1.0, 0.05)
    traffic_scale = st.slider("Traffic severity", 0.6, 1.8, 1.0, 0.05)
    planning_horizon = st.selectbox("Planning horizon", ["Next 2 hours", "Next 4 hours", "Next 8 hours"], index=1)
    st.divider()
    st.markdown("**Optimization objective**")
    objective = st.selectbox("Priority", ["Balanced", "Minimize late deliveries", "Minimize operating cost"])
    st.caption("Live API connectors can be configured in `.env` when credentials are available.")

snapshot = make_live_snapshot(orders, zones, demand_scale, traffic_scale, seed=None if refresh else 42)
predictions = predict_zone_demand(model, snapshot, horizon=planning_horizon)
allocations, allocation_meta = allocate_fleet(predictions, fleet, objective=objective)
route_summary = build_route_summary(allocations, snapshot, fleet)

total_demand = int(predictions["predicted_orders"].sum())
allocated = int(allocations["assigned_orders"].sum()) if len(allocations) else 0
active_vehicles = int((allocations["vehicles_assigned"] > 0).sum()) if len(allocations) else 0
coverage = min(100, round(100 * allocated / max(total_demand, 1)))
avg_traffic = round(float(snapshot["traffic_index"].mean()), 0)
late_risk = round(float(allocations["late_risk_pct"].mean()), 1) if len(allocations) else 0

m1,m2,m3,m4,m5 = st.columns(5)
m1.metric("Forecast demand", f"{total_demand:,}", help="Predicted orders in the selected horizon")
m2.metric("Orders covered", f"{allocated:,}", f"{coverage}% coverage")
m3.metric("Vehicles deployed", f"{active_vehicles}/{len(fleet)}")
m4.metric("Avg. traffic index", f"{avg_traffic:.0f}/100")
m5.metric("Estimated late risk", f"{late_risk:.1f}%")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🗺️ Live Operations", "🚚 Fleet Allocation", "🧠 Demand Forecast", "🛣️ Route Planning", "📊 Performance", "📥 Project Downloads"])

with tab1:
    left, right = st.columns([1.65,1])
    with left:
        st.subheader("Delivery zones & operating conditions")
        center = [float(zones["lat"].mean()), float(zones["lon"].mean())]
        fmap = folium.Map(location=center, zoom_start=11, tiles="CartoDB positron")
        joined = predictions.drop(
            columns=["traffic_index", "congestion"],
            errors="ignore"
        ).merge(
            snapshot[["zone_id", "traffic_index", "congestion"]],
            on="zone_id",
            how="left"
        )
        for _, row in joined.iterrows():
            color = "#dc2626" if row["congestion"] == "High" else ("#d97706" if row["congestion"] == "Medium" else "#16a34a")
            folium.CircleMarker(
                [row["lat"],row["lon"]], radius=7 + min(10, row["predicted_orders"]/12),
                color=color, fill=True, fill_opacity=.72,
                popup=f'{row["zone_name"]}: {int(row["predicted_orders"])} orders · traffic {int(row["traffic_index"])}'
            ).add_to(fmap)
            folium.Marker([row["lat"],row["lon"]], icon=folium.DivIcon(html=f'<div style="font-size:10px;font-weight:700;color:#111827">{row["zone_name"]}</div>')).add_to(fmap)
        st_folium(fmap, width=None, height=490, returned_objects=[])
    with right:
        st.subheader("Demand vs. traffic")
        fig = px.scatter(joined, x="traffic_index", y="predicted_orders", size="predicted_orders",
                         color="congestion", hover_name="zone_name",
                         color_discrete_map={"Low":"#16a34a","Medium":"#d97706","High":"#dc2626"},
                         labels={"traffic_index":"Traffic index","predicted_orders":"Forecast orders","congestion":"Congestion"})
        fig.update_layout(height=300, margin=dict(l=5,r=5,t=20,b=5))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("**Operational signals**")
        for _, r in joined.sort_values("predicted_orders", ascending=False).head(5).iterrows():
            st.write(f"**{r.zone_name}** · {int(r.predicted_orders)} orders · {r.congestion} traffic")
        st.info("Marker size represents forecast demand. Red, amber and green indicate high, medium and low congestion.")

with tab2:
    st.subheader("Recommended fleet allocation")
    st.caption("The allocator respects vehicle capacity and uses traffic-adjusted service capacity.")
    show = allocations[["zone_name","predicted_orders","vehicles_assigned","assigned_orders","unserved_orders","traffic_index","late_risk_pct","allocation_reason"]].copy()
    show.columns = ["Zone","Forecast orders","Vehicles","Orders covered","Unserved","Traffic index","Late risk %","Allocation rationale"]
    st.dataframe(show, use_container_width=True, hide_index=True)
    c1,c2 = st.columns(2)
    with c1:
        fig = px.bar(allocations, x="zone_name", y=["assigned_orders","unserved_orders"], barmode="stack",
                     labels={"zone_name":"Zone","value":"Orders","variable":"Coverage"},
                     color_discrete_sequence=["#2563eb","#f59e0b"])
        fig.update_layout(height=340, margin=dict(l=5,r=5,t=20,b=5))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.pie(allocations[allocations.vehicles_assigned>0], names="zone_name", values="vehicles_assigned",
                     hole=.55, title="Vehicle distribution by zone")
        fig.update_layout(height=340, margin=dict(l=5,r=5,t=45,b=5))
        st.plotly_chart(fig, use_container_width=True)
    st.success(f"Allocation complete: {allocated:,} of {total_demand:,} forecast orders covered using {active_vehicles} active vehicles.")
    st.caption(f"Solver: {allocation_meta['solver']} · Objective: {allocation_meta['objective']} · {allocation_meta['notes']}")

with tab3:
    st.subheader("Machine-learning demand forecast")
    st.write("A Random Forest regression model estimates zone-level order volume from time, day, historical demand and local conditions. Demo training data is synthetic.")
    a,b,c = st.columns(3)
    a.metric("Model", "Random Forest")
    b.metric("Validation MAE", f"{metrics['mae']:.1f} orders")
    c.metric("Validation R²", f"{metrics['r2']:.2f}")
    chart = px.bar(predictions.sort_values("predicted_orders",ascending=False), x="zone_name", y="predicted_orders",
                   color="predicted_orders", color_continuous_scale="Blues", labels={"zone_name":"Delivery zone","predicted_orders":"Predicted orders"})
    chart.update_layout(height=380, margin=dict(l=5,r=5,t=20,b=5))
    st.plotly_chart(chart, use_container_width=True)
    st.dataframe(predictions[["zone_name","historical_avg_orders","predicted_orders","demand_level"]], use_container_width=True, hide_index=True)
    st.warning("Model quality is illustrative because the demo dataset is generated. Replace it with timestamped historical order data before operational use.")

with tab4:
    st.subheader("Route planning overview")
    st.write("Routes are represented as zone-level plans. The demo uses haversine distance and traffic-adjusted travel-time estimates; connect a routing provider for road-network directions.")
    st.dataframe(route_summary, use_container_width=True, hide_index=True)
    if len(route_summary):
        fig = px.bar(route_summary, x="zone_name", y="estimated_travel_minutes", color="congestion",
                     color_discrete_map={"Low":"#16a34a","Medium":"#d97706","High":"#dc2626"},
                     labels={"zone_name":"Zone","estimated_travel_minutes":"Estimated travel (minutes)"})
        fig.update_layout(height=330, margin=dict(l=5,r=5,t=20,b=5))
        st.plotly_chart(fig, use_container_width=True)

with tab5:
    st.subheader("Operational performance")
    p1,p2,p3 = st.columns(3)
    p1.metric("Fleet utilization", f"{100*allocations.vehicles_assigned.sum()/max(len(fleet),1):.0f}%")
    p2.metric("Unserved demand", f"{int(allocations.unserved_orders.sum()):,} orders")
    p3.metric("Average zone late risk", f"{late_risk:.1f}%")
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Forecast", x=allocations.zone_name, y=allocations.predicted_orders))
    fig.add_trace(go.Bar(name="Covered", x=allocations.zone_name, y=allocations.assigned_orders))
    fig.update_layout(barmode="group", height=360, yaxis_title="Orders", xaxis_title="Zone")
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("**How to interpret this demo**")
    st.markdown("- Coverage = assigned orders / forecast orders.\n- Late risk is a heuristic based on congestion and load pressure, not a guaranteed SLA prediction.\n- Cost and fuel savings should be calculated after adding actual vehicle cost, fuel and route data.")


with tab6:
    st.subheader("Project files")
    st.write("Download the academic submission materials directly from this Streamlit app.")

    project_dir = Path(__file__).resolve().parent

    # Build a clean source archive in memory; omit caches and virtual environments.
    source_buffer = io.BytesIO()
    excluded_dirs = {".git", ".venv", "venv", "__pycache__", ".pytest_cache"}
    excluded_suffixes = {".pyc", ".pyo"}
    with zipfile.ZipFile(source_buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file_path in sorted(project_dir.rglob("*")):
            if not file_path.is_file():
                continue
            relative = file_path.relative_to(project_dir)
            if any(part in excluded_dirs for part in relative.parts):
                continue
            if file_path.suffix in excluded_suffixes:
                continue
            archive.write(file_path, arcname=Path("adaptive_last_mile_delivery") / relative)
    source_buffer.seek(0)

    d1, d2 = st.columns(2)
    with d1:
        abstract_docx = project_dir / "Adaptive_Last_Mile_Delivery_Abstract.docx"
        if abstract_docx.exists():
            st.download_button(
                "⬇️ Download Abstract (Word)",
                data=abstract_docx.read_bytes(),
                file_name=abstract_docx.name,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
            )
        abstract_md = project_dir / "ABSTRACT.md"
        if abstract_md.exists():
            st.download_button(
                "⬇️ Download Abstract (Markdown)",
                data=abstract_md.read_bytes(),
                file_name=abstract_md.name,
                mime="text/markdown",
                use_container_width=True,
            )
    with d2:
        presentation = project_dir / "Adaptive_Last_Mile_Delivery_Presentation.pptx"
        if presentation.exists():
            st.download_button(
                "⬇️ Download Presentation (PPTX)",
                data=presentation.read_bytes(),
                file_name=presentation.name,
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                use_container_width=True,
            )
        st.download_button(
            "⬇️ Download Complete Source Code (ZIP)",
            data=source_buffer.getvalue(),
            file_name="Adaptive_Last_Mile_Delivery_Source_Code.zip",
            mime="application/zip",
            use_container_width=True,
        )

    st.info("This demo uses synthetic demand and traffic data. The downloads contain the project source and academic materials; live traffic APIs are not enabled by default.")

with st.expander("Data dictionary & assumptions"):
    st.markdown("""
    - **Traffic index:** simulated 0–100 congestion score.
    - **Zone demand:** predicted order count for the selected horizon.
    - **Vehicle capacity:** nominal number of parcels a vehicle can carry in one planning window.
    - **Service capacity:** capacity reduced by congestion and operating conditions.
    - **Unserved demand:** forecast demand not covered by available fleet.
    - This prototype is a decision-support demo, not an autonomous dispatch system.
    """)
st.divider()
st.caption("Adaptive Last-Mile Delivery Fleet Allocation · Prototype · Synthetic data · Built with Streamlit")
