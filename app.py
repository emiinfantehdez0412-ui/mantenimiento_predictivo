import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from statsmodels.tsa.holtwinters import ExponentialSmoothing

# ============================================
# CONFIG
# ============================================
st.set_page_config(page_title="Dashboard de Mantenimiento Predictivo", layout="wide")

st.title("🛠️ Dashboard de Mantenimiento Predictivo")
st.write("---")

# ============================================
# UPLOAD FILES
# ============================================
st.sidebar.header("📂 Carga de archivos")

file_original = st.sidebar.file_uploader("Sube la base ORIGINAL (Mantenimiento_FLEX.xlsx)", type=["xlsx"])
file_final = st.sidebar.file_uploader("Sube la tabla PROCESADA (final_table.xlsx)", type=["xlsx"])

if file_original:
    df_original = pd.read_excel(file_original)
    st.sidebar.success("Base original cargada correctamente. ✔")

if file_final:
    df_final = pd.read_excel(file_final)
    st.sidebar.success("Tabla procesada cargada correctamente. ✔")

# Stop here if no files
if not file_original or not file_final:
    st.warning("Por favor sube ambos archivos para continuar.")
    st.stop()

# ============================================
# CLEAN COLUMN NAMES
# ============================================
df_original.columns = df_original.columns.str.strip()
df_final.columns = df_final.columns.str.strip()

# ============================================
# SIDEBAR FILTERS
# ============================================
st.sidebar.header("🎛️ Filtros")

clusters = sorted(df_final["Cluster"].unique())
cluster_sel = st.sidebar.selectbox("Selecciona un clúster:", clusters)

machines = sorted(df_final[df_final["Cluster"] == cluster_sel]["Machine"].unique())
machine_sel = st.sidebar.selectbox("Selecciona una máquina:", machines)

shifts = ["Todos"] + sorted(df_original["Shift"].astype(str).unique())
shift_sel = st.sidebar.selectbox("Selecciona turno (Shift):", shifts)

eq_types = ["Todos"] + sorted(df_original["EQ Type"].astype(str).unique())
eq_sel = st.sidebar.selectbox("Selecciona EQ Type:", eq_types)

# ============================================
# FILTER ORIGINAL DATA
# ============================================
df_machine = df_original[df_original["Machine Name"] == machine_sel].copy()

if shift_sel != "Todos":
    df_machine = df_machine[df_machine["Shift"] == shift_sel]

if eq_sel != "Todos":
    df_machine = df_machine[df_machine["EQ Type"] == eq_sel]

# ============================================
# HISTORICAL WEEKLY FAILURES
# ============================================
df_machine["Date"] = pd.to_datetime(df_machine["Date"])
df_machine = df_machine.sort_values("Date")

weekly_failures = df_machine.groupby(pd.Grouper(key="Date", freq="W")).size()

# ============================================
# CROSTON FORECAST
# ============================================
def croston(ts):
    ts = np.array(ts)
    n = len(ts)
    a, p = 0.3, 0.3
    level, interval = ts[0], 1
    next_event = 1 if ts[0] > 0 else 0

    for i in range(1, n):
        if ts[i] > 0:
            level = level + a * (ts[i] - level)
            interval = interval + p * (next_event - interval)
            next_event = 1
        else:
            next_event = 0

    forecast = level / interval if interval != 0 else 0
    return forecast

croston_pred = croston(weekly_failures.values)

# ============================================
# TSB FORECAST
# ============================================
def tsb(ts, alpha=0.3, beta=0.3):
    ts = np.array(ts)
    n = len(ts)
    demand = np.where(ts > 0, 1, 0)

    p = demand[0]
    l = ts[0]

    for i in range(1, n):
        p = p + alpha * (demand[i] - p)
        l = l + beta * (ts[i] - l)

    return p * l

tsb_pred = tsb(weekly_failures.values)

# ============================================
# GET METRICS FROM FINAL TABLE
# ============================================
row = df_final[df_final["Machine"] == machine_sel].iloc[0]

MAE_Croston = row["MAE_Croston"]
RMSE_Croston = row["RMSE_Croston"]
MASE_Croston = row["MASE_Croston"]

MAE_TSB = row["MAE_TSB"]
RMSE_TSB = row["RMSE_TSB"]
MASE_TSB = row["MASE_TSB"]

maint = row["Maintenance_Recommended"]

# ============================================
# MAINTENANCE MESSAGE
# ============================================
st.subheader("🛠️ Mantenimiento recomendado")
st.success(f"✔ Se recomienda mantenimiento en **{maint}**.")

st.write("---")

# ============================================
# PLOT HISTORICAL + FORECAST
# ============================================
st.subheader("📈 Tendencia histórica y predicción (TSB & Croston)")

fig = go.Figure()

# Histórico
fig.add_trace(go.Scatter(
    x=weekly_failures.index,
    y=weekly_failures.values,
    mode="lines+markers",
    name="Histórico",
    line=dict(color="#00FFFF")
))

# Croston
fig.add_trace(go.Scatter(
    x=[weekly_failures.index.max() + pd.Timedelta(days=7)],
    y=[croston_pred],
    mode="markers",
    name="Predicción Croston",
    marker=dict(size=12, color="#FF00FF")
))

# TSB
fig.add_trace(go.Scatter(
    x=[weekly_failures.index.max() + pd.Timedelta(days=7)],
    y=[tsb_pred],
    mode="markers",
    name="Predicción TSB",
    marker=dict(size=12, color="yellow")
))

st.plotly_chart(fig, use_container_width=True)

st.write("---")

# ============================================
# METRICS
# ============================================
st.subheader("📊 Métricas de error (MAE / RMSE / MASE)")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📌 Croston")
    st.write(f"**MAE:** {MAE_Croston:.4f}")
    st.write(f"**RMSE:** {RMSE_Croston:.4f}")
    st.write(f"**MASE:** {MASE_Croston:.4f}")

with col2:
    st.markdown("### 📌 TSB")
    st.write(f"**MAE:** {MAE_TSB:.4f}")
    st.write(f"**RMSE:** {RMSE_TSB:.4f}")
    st.write(f"**MASE:** {MASE_TSB:.4f}")

st.success("Dashboard generado correctamente. ✔")
