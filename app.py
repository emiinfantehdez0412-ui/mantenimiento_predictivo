import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ===========================
# 1. CONFIG
# ===========================
st.set_page_config(page_title="Dashboard Predictivo", layout="wide")

st.title("🛠️ Dashboard de Mantenimiento Predictivo")

# ===========================
# 2. SUBIDA DE ARCHIVOS
# ===========================
st.sidebar.header("📂 Carga de archivos")

file_original = st.sidebar.file_uploader(
    "Sube la base ORIGINAL (Mantenimiento_FLEX.xlsx)", type=["xlsx"]
)

file_final = st.sidebar.file_uploader(
    "Sube la tabla PROCESADA (final_table.xlsx)", type=["xlsx"]
)

if file_original:
    df_original = pd.read_excel(file_original)
    st.sidebar.success("Base original cargada correctamente. ✔️")

if file_final:
    final = pd.read_excel(file_final)
    st.sidebar.success("Tabla procesada cargada correctamente. ✔️")

# No continuar hasta tener ambas
if not file_original or not file_final:
    st.warning("Sube ambos archivos para continuar.")
    st.stop()

# ===========================
# 3. PREPROCESAMIENTO NECESARIO
# ===========================
df_original["Date"] = pd.to_datetime(df_original["Date"])
df_original["Week"] = df_original["Date"].dt.to_period("W").dt.start_time

# ===========================
# 4. FILTROS (CORREGIDOS)
# ===========================
st.sidebar.header("🎛️ Filtros")

# Clusters provienen SOLO del archivo final
clusters = sorted(final["Cluster"].unique())
cluster_sel = st.sidebar.selectbox("Selecciona un clúster:", clusters)

# Máquinas que pertenecen al cluster (según final_table)
machines_cluster = final[final["Cluster"] == cluster_sel]["Machine"].unique()
machine_sel = st.sidebar.selectbox("Selecciona una máquina:", machines_cluster)

# Filtramos la base original por la máquina seleccionada
df_filt_machine = df_original[df_original["Machine Name"] == machine_sel].copy()

# Shift y EQ Type
shifts = ["Todos"] + sorted(df_original["Shift"].unique())
shift_sel = st.sidebar.selectbox("Selecciona turno (Shift):", shifts)

eq_types = ["Todos"] + sorted(df_original["EQ Type"].unique())
eq_sel = st.sidebar.selectbox("Selecciona EQ Type:", eq_types)

# Aplicar filtros
if shift_sel != "Todos":
    df_filt_machine = df_filt_machine[df_filt_machine["Shift"] == shift_sel]

if eq_sel != "Todos":
    df_filt_machine = df_filt_machine[df_filt_machine["EQ Type"] == eq_sel]

# ===========================
# 5. MANTENIMIENTO RECOMENDADO
# ===========================
st.subheader("🛠️ Mantenimiento recomendado")

try:
    maint = final[final["Machine"] == machine_sel]["Maintenance_Recommended"].values[0]
    st.success(f"✔️ Se recomienda mantenimiento en **{maint}**.")
except:
    st.warning("No hay información de mantenimiento.")

# ===========================
# 6. TENDENCIA POR CLÚSTER
# ===========================
st.subheader("📊 Tendencia histórica y predicción por CLÚSTER")

df_cluster = df_original[df_original["Cluster"] == cluster_sel].copy()
weekly_cluster = df_cluster.groupby("Week")["Downtime"].sum().reset_index()

cluster_pred = final[final["Cluster"] == cluster_sel]["Weekly_Prediction"].mean()

fig_c = go.Figure()
fig_c.add_trace(go.Scatter(
    x=weekly_cluster["Week"],
    y=weekly_cluster["Downtime"],
    name="Histórico",
    mode="lines+markers",
    line=dict(color="#00e5ff")
))
fig_c.add_trace(go.Scatter(
    x=[weekly_cluster["Week"].max() + pd.Timedelta(days=7)],
    y=[cluster_pred],
    name="Predicción",
    mode="markers",
    marker=dict(size=12, color="yellow")
))
st.plotly_chart(fig_c, use_container_width=True)

# ===========================
# 7. TENDENCIA POR MÁQUINA (HISTÓRICO + CROSTON + TSB)
# ===========================
st.subheader("📈 Tendencia histórica y predicción por MÁQUINA (TSB & Croston)")

weekly_machine = df_filt_machine.groupby("Week")["Downtime"].sum().reset_index()

try:
    pred_best = final[final["Machine"] == machine_sel]["Weekly_Prediction"].values[0]
except:
    pred_best = 0

fig_m = go.Figure()
fig_m.add_trace(go.Scatter(
    x=weekly_machine["Week"],
    y=weekly_machine["Downtime"],
    mode="lines+markers",
    name="Histórico",
    line=dict(color="#00e5ff")
))

fig_m.add_trace(go.Scatter(
    x=[weekly_machine["Week"].max() + pd.Timedelta(days=7)],
    y=[pred_best],
    mode="markers",
    marker=dict(color="yellow", size=12),
    name="Predicción TSB"
))

st.plotly_chart(fig_m, use_container_width=True)

# ===========================
# 8. EQ TYPE QUE MÁS FALLAS GENERA
# ===========================
st.subheader("⚙️ EQ Type que genera más fallas")

eq_rank = (
    df_filt[df_filt["Machine Name"] == machine_sel]
    .groupby("EQ Type")["Downtime"]
    .sum()
    .sort_values(ascending=False)
)

if len(eq_rank) > 0:
    worst_eq = eq_rank.idxmax()
    worst_val = eq_rank.max()
    st.info(f"🔧 El EQ Type que más fallas genera es **{worst_eq}** con **{worst_val:.2f} horas** de downtime total.")
else:
    st.warning("No hay datos suficientes para EQ Type.")

fig_eq = go.Figure()
fig_eq.add_trace(go.Bar(
    x=eq_rank.index,
    y=eq_rank.values,
    marker_color="#ff6b6b"
))
st.plotly_chart(fig_eq, use_container_width=True)

# ===========================
# 9. MÉTRICAS DEL MODELO
# ===========================
st.subheader("📐 Métricas de error del modelo (MAE)")

try:
    row = final[final["Machine"] == machine_sel].iloc[0]
    col1, col2, col3 = st.columns(3)
    col1.metric("MAE Croston", round(row["MAE_Croston"], 4))
    col2.metric("MAE TSB", round(row["MAE_TSB"], 4))
    col3.metric("Mejor Modelo", row["Best_Model"])
except:
    st.warning("No hay métricas disponibles para esta máquina.")

# ===========================
# 10. MENSAJE FINAL
# ===========================
st.success("Dashboard generado correctamente. ✔️")
