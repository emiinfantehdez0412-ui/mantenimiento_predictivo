import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Dashboard de Mantenimiento Predictivo", layout="wide")

st.title("🛠️ Dashboard de Mantenimiento Predictivo")

# ============================================================
# 1. CARGA DE ARCHIVOS
# ============================================================

st.sidebar.header("📂 Carga de archivos")

uploaded_original = st.sidebar.file_uploader("Sube la base ORIGINAL (Mantenimiento_FLEX.xlsx)", type=["xlsx"])
uploaded_final = st.sidebar.file_uploader("Sube la tabla PROCESADA (final_table.xlsx)", type=["xlsx"])

if uploaded_original:
    df_original = pd.read_excel(uploaded_original)
    st.sidebar.success("Base original cargada correctamente. ✓")
else:
    st.stop()

if uploaded_final:
    df_final = pd.read_excel(uploaded_final)
    st.sidebar.success("Tabla procesada cargada correctamente. ✓")
else:
    st.stop()

# ============================================================
# 2. NORMALIZACIÓN Y UNIFICACIÓN DE MACHINE + CLUSTER
# ============================================================

df_original["Machine Name"] = df_original["Machine Name"].astype(str).str.strip().str.lower()
df_final["Machine"] = df_final["Machine"].astype(str).str.strip().str.lower()

df_cluster_map = df_final[["Machine", "Cluster"]].drop_duplicates()

df_original = df_original.merge(
    df_cluster_map,
    left_on="Machine Name",
    right_on="Machine",
    how="left"
)

df_original.drop(columns=["Machine"], inplace=True)

if df_original["Cluster"].isna().all():
    st.error("❌ No se pudieron unir los clústeres. Revisa los nombres de máquina.")
    st.stop()

# ============================================================
# 3. NORMALIZAR FECHA + CREAR FALLAS (opción A)
# ============================================================

if "Fecha" in df_original.columns:
    df_original.rename(columns={"Fecha": "Date"}, inplace=True)

df_original["Date"] = pd.to_datetime(df_original["Date"], errors="coerce")

# 👉 Opción A: cada fila = 1 falla
df_original["Failures"] = 1

# ============================================================
# 4. FILTROS
# ============================================================

st.sidebar.header("🎛️ Filtros")

cluster_list = sorted(df_original["Cluster"].dropna().unique())
cluster_sel = st.sidebar.selectbox("Selecciona un clúster:", cluster_list)

machines_list = sorted(df_original[df_original["Cluster"] == cluster_sel]["Machine Name"].unique())
machine_sel = st.sidebar.selectbox("Selecciona una máquina:", machines_list)

shift_list = sorted(df_original["Shift"].dropna().unique())
shift_sel = st.sidebar.selectbox("Selecciona turno (Shift):", ["Todos"] + list(shift_list))

eq_types = df_original["EQ Type"].dropna().unique()
eq_sel = st.sidebar.selectbox("Selecciona EQ Type:", ["Todos"] + list(eq_types))

df_filt = df_original.copy()

if shift_sel != "Todos":
    df_filt = df_filt[df_filt["Shift"] == shift_sel]

if eq_sel != "Todos":
    df_filt = df_filt[df_filt["EQ Type"] == eq_sel]

# ============================================================
# 5. MANTENIMIENTO RECOMENDADO
# ============================================================

try:
    rec_days = float(df_final["Weekly_Prediction"].mean())
    st.success(f"🟢 Mantenimiento recomendado en **{round(rec_days,1)} días**.")
except:
    st.warning("No se pudo calcular el mantenimiento recomendado.")

# ============================================================
# 6. GRÁFICO POR MÁQUINA (histórico + predicciones)
# ============================================================

st.subheader(f"📉 Tendencia histórica y predicción (TSB & Croston) – Máquina: {machine_sel}")

df_machine = df_filt[df_filt["Machine Name"] == machine_sel].copy()
df_machine = df_machine.sort_values("Date")

df_machine_grouped = df_machine.groupby("Date")["Failures"].sum()

# Extraer predicciones
try:
    row = df_final[df_final["Machine"] == machine_sel].iloc[0]
    pred_tsb = row["Weekly_Prediction"]
    pred_cros = row["Weekly_Prediction"]  # si hay otra columna cámbiala
except:
    pred_tsb = pred_cros = None

fig_m = go.Figure()

fig_m.add_trace(go.Scatter(
    x=df_machine_grouped.index,
    y=df_machine_grouped.values,
    mode="lines+markers",
    name="Histórico de Fallas",
    line=dict(color="#00e5ff")
))

if pred_cros is not None:
    fig_m.add_trace(go.Scatter(
        x=[df_machine_grouped.index.max() + pd.Timedelta(days=7)],
        y=[pred_cros],
        mode="markers",
        name="Predicción Croston",
        marker=dict(color="magenta", size=12)
    ))

if pred_tsb is not None:
    fig_m.add_trace(go.Scatter(
        x=[df_machine_grouped.index.max() + pd.Timedelta(days=7)],
        y=[pred_tsb],
        mode="markers",
        name="Predicción TSB",
        marker=dict(color="yellow", size=12)
    ))

fig_m.update_layout(height=350, xaxis_title="Fecha", yaxis_title="Fallas")
st.plotly_chart(fig_m, use_container_width=True)

# ============================================================
# 7. GRÁFICO POR CLÚSTER
# ============================================================

st.subheader(f"📊 Tendencia histórica por CLÚSTER – {cluster_sel}")

df_cluster = df_filt[df_filt["Cluster"] == cluster_sel].copy()
df_cluster_grouped = df_cluster.groupby("Date")["Failures"].sum()

fig_c = go.Figure()

fig_c.add_trace(go.Scatter(
    x=df_cluster_grouped.index,
    y=df_cluster_grouped.values,
    mode="lines+markers",
    name="Histórico Cluster",
    line=dict(color="orange")
))

try:
    pred_cluster = df_final[df_final["Cluster"] == cluster_sel]["Weekly_Prediction"].mean()
    fig_c.add_trace(go.Scatter(
        x=[df_cluster_grouped.index.max() + pd.Timedelta(days=7)],
        y=[pred_cluster],
        mode="markers",
        name="Predicción Cluster",
        marker=dict(color="yellow", size=12)
    ))
except:
    pass

fig_c.update_layout(height=350, xaxis_title="Fecha", yaxis_title="Fallas")
st.plotly_chart(fig_c, use_container_width=True)

# ============================================================
# 8. MÉTRICAS
# ============================================================

st.subheader("📐 Métricas del modelo")

try:
    row = df_final[df_final["Machine"] == machine_sel].iloc[0]
    col1, col2, col3 = st.columns(3)

    col1.metric("MAE Croston", round(row["MAE_Croston"], 3))
    col2.metric("MAE TSB", round(row["MAE_TSB"], 3))
    col3.metric("Mejor Modelo", "Croston" if row["MAE_Croston"] <= row["MAE_TSB"] else "TSB")

except:
    st.warning("No hay métricas disponibles para esta máquina.")
