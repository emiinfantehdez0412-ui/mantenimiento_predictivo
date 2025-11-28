import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import timedelta

st.set_page_config(page_title="Dashboard Predictivo", layout="wide")


# -----------------------------------------------------------
# 1. CARGA DE ARCHIVOS
# -----------------------------------------------------------

st.sidebar.header("📤 Carga de archivos")

file_original = st.sidebar.file_uploader(
    "Sube la base ORIGINAL (Mantenimiento_FLEX.xlsx)",
    type=["xlsx"]
)

file_final = st.sidebar.file_uploader(
    "Sube la tabla PROCESADA (Final_Table.xlsx)",
    type=["xlsx"]
)


# si no hay archivos, no sigue
if file_original is None or file_final is None:
    st.title("🔧 Dashboard de Mantenimiento Predictivo")
    st.warning("Sube ambos archivos para continuar.")
    st.stop()

df_original = pd.read_excel(file_original)
df_final = pd.read_excel(file_final)

st.sidebar.success("Base original cargada correctamente. ✓")
st.sidebar.success("Tabla procesada cargada correctamente. ✓")


# -----------------------------------------------------------
# 2. FILTROS
# -----------------------------------------------------------

st.sidebar.header("🎛️ Filtros")

clusters = sorted(df_final["Cluster"].unique())
cluster_sel = st.sidebar.selectbox("Selecciona un clúster:", clusters)

machines = sorted(df_final[df_final["Cluster"] == cluster_sel]["Machine"].unique())
machine_sel = st.sidebar.selectbox("Selecciona una máquina:", machines)

shifts = ["Todos"] + sorted(df_original["Shift"].astype(str).unique())
shift_sel = st.sidebar.selectbox("Selecciona turno (Shift):", shifts)

eq_types = ["Todos"] + sorted(df_original["EQ Type"].astype(str).unique())
eq_sel = st.sidebar.selectbox("Selecciona EQ Type:", eq_types)


# -----------------------------------------------------------
# FILTROS APLICADOS SOBRE LA BASE ORIGINAL
# -----------------------------------------------------------

df_filtered = df_original.copy()

df_filtered = df_filtered[df_filtered["Machine Name"] == machine_sel]

if shift_sel != "Todos":
    df_filtered = df_filtered[df_filtered["Shift"].astype(str) == shift_sel]

if eq_sel != "Todos":
    df_filtered = df_filtered[df_filtered["EQ Type"].astype(str) == eq_sel]


# -----------------------------------------------------------
# INFORMACIÓN DE LA TABLA FINAL (MÉTRICAS Y PREDICCIÓN)
# -----------------------------------------------------------

machine_row = df_final[df_final["Machine"] == machine_sel].iloc[0]

weekly_pred = machine_row["Weekly_Prediction"]
maint_rec = machine_row["Maintenance_Recommended"]

mae_croston = machine_row["MAE_Croston"]
mae_tsb = machine_row["MAE_TSB"]
rmse_croston = machine_row["RMSE_Croston"]
rmse_tsb = machine_row["RMSE_TSB"]
mase_croston = machine_row["MASE_Croston"]
mase_tsb = machine_row["MASE_TSB"]


# -----------------------------------------------------------
# ENCABEZADO GENERAL
# -----------------------------------------------------------

st.title("🔧 Dashboard de Mantenimiento Predictivo")

# -----------------------------------------------------------
# RECOMENDACIÓN DE MANTENIMIENTO
# -----------------------------------------------------------

st.subheader("🛠️ Mantenimiento recomendado")

st.success(f"➡️ Se recomienda mantenimiento en **{maint_rec}**.")


# -----------------------------------------------------------
# 3. GRÁFICO POR MÁQUINA (HISTÓRICO + PREDICCIONES)
# -----------------------------------------------------------

st.subheader(f"📈 Tendencia histórica y predicción (TSB & Croston) – Máquina: {machine_sel}")

df_machine = df_filtered.copy()

if df_machine.empty:
    st.warning("No hay datos históricos para esta máquina con los filtros aplicados.")
else:
    df_machine = df_machine.sort_values("Date")

    fig_machine = go.Figure()

    # Histórico
    fig_machine.add_trace(go.Scatter(
        x=df_machine["Date"],
        y=df_machine["Downtime"],
        mode="lines+markers",
        name="Histórico",
        line=dict(color="#00FFFF", width=2)
    ))

    # Predicción Croston
    fig_machine.add_trace(go.Scatter(
        x=[df_machine["Date"].max() + timedelta(days=7)],
        y=[weekly_pred],
        mode="markers",
        name="Predicción Croston",
        marker=dict(color="magenta", size=12)
    ))

    # Predicción TSB (si quieres usar otra columna)
    fig_machine.add_trace(go.Scatter(
        x=[df_machine["Date"].max() + timedelta(days=7)],
        y=[weekly_pred],
        mode="markers",
        name="Predicción TSB",
        marker=dict(color="yellow", size=12)
    ))

    fig_machine.update_layout(
        template="plotly_dark",
        xaxis_title="Fecha",
        yaxis_title="Fallas estimadas",
        height=400
    )

    st.plotly_chart(fig_machine, use_container_width=True)


# -----------------------------------------------------------
# 4. GRÁFICO POR CLÚSTER (HISTÓRICO + PREDICCIÓN)
# -----------------------------------------------------------

st.subheader(f"📊 Tendencia histórica y predicción por CLÚSTER – {cluster_sel}")

df_cluster = df_original[df_original["Machine Name"].isin(
    df_final[df_final["Cluster"] == cluster_sel]["Machine"].unique()
)]

if df_cluster.empty:
    st.warning("No hay datos disponibles para este clúster.")
else:
    df_cluster = df_cluster.sort_values("Date")
    df_cluster_weekly = df_cluster.groupby("Date")["Downtime"].sum().reset_index()

    pred_cluster = df_final[df_final["Cluster"] == cluster_sel]["Weekly_Prediction"].mean()

    fig_cluster = go.Figure()

    fig_cluster.add_trace(go.Scatter(
        x=df_cluster_weekly["Date"],
        y=df_cluster_weekly["Downtime"],
        mode="lines+markers",
        name="Histórico Cluster",
        line=dict(color="#FFD700", width=2)
    ))

    fig_cluster.add_trace(go.Scatter(
        x=[df_cluster_weekly["Date"].max() + timedelta(days=7)],
        y=[pred_cluster],
        mode="markers",
        name="Predicción Cluster",
        marker=dict(color="orange", size=12)
    ))

    fig_cluster.update_layout(
        template="plotly_dark",
        xaxis_title="Fecha",
        yaxis_title="Fallas estimadas",
        height=400
    )

    st.plotly_chart(fig_cluster, use_container_width=True)


# -----------------------------------------------------------
# 5. MÉTRICAS DEL MODELO
# -----------------------------------------------------------

st.subheader("📊 Métricas del modelo (MAE / RMSE / MASE)")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("MAE Croston", round(mae_croston, 4))
    st.metric("RMSE Croston", round(rmse_croston, 4))
    st.metric("MASE Croston", round(mase_croston, 4))

with col2:
    st.metric("MAE TSB", round(mae_tsb, 4))
    st.metric("RMSE TSB", round(rmse_tsb, 4))
    st.metric("MASE TSB", round(mase_tsb, 4))

with col3:
    better = "Croston" if mae_croston < mae_tsb else "TSB"
    st.success(f"🏆 Mejor modelo: **{better}**")
