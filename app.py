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
    df_original = None

if uploaded_final:
    df_final = pd.read_excel(uploaded_final)
    st.sidebar.success("Tabla procesada cargada correctamente. ✓")
else:
    df_final = None

if df_original is None or df_final is None:
    st.warning("Carga ambos archivos para continuar.")
    st.stop()

# ============================================================
# *** UNIFICAR CLUSTER EN LA BASE ORIGINAL ***
# ============================================================

# Normalizar nombres de máquina en ambas bases
df_original["Machine Name"] = df_original["Machine Name"].astype(str).str.strip().str.lower()
df_final["Machine"] = df_final["Machine"].astype(str).str.strip().str.lower()

# Tomar solo columnas de cluster de df_final
df_cluster_map = df_final[["Machine", "Cluster"]].drop_duplicates()

# Hacer merge para unir cluster a la base original
df_original = df_original.merge(
    df_cluster_map,
    left_on="Machine Name",
    right_on="Machine",
    how="left"
)

# Eliminar columna duplicada
df_original.drop(columns=["Machine"], inplace=True)

# Validar que ya existe Cluster
if df_original["Cluster"].isna().all():
    st.error("❌ ERROR: No se pudieron asignar los clusters a la base original. Revisa que los nombres de máquina coincidan entre ambos Excel.")
    st.stop()
    
# ============================================================
# 2. NORMALIZAR NOMBRE DE FECHA
# ============================================================

if "Fecha" in df_original.columns:
    df_original.rename(columns={"Fecha": "Date"}, inplace=True)

if "Date" in df_original.columns:
    df_original["Date"] = pd.to_datetime(df_original["Date"], errors="coerce")
# ============================================================
# Normalizar columna Cluster
# ============================================================

cluster_cols = [c for c in df_original.columns if c.lower().strip() in ["cluster", "clúster", "clusters"]]

if len(cluster_cols) == 0:
    st.error(
        "❌ ERROR: Tu base original NO tiene una columna llamada 'Cluster'.\n\n"
        "Revisa tu Excel y asegúrate de que tenga una columna con alguno de estos nombres:\n"
        "- Cluster\n- cluster\n- Clúster\n\n"
        "La tabla final SÍ la tiene, pero la original NO."
    )
    st.stop()

df_original.rename(columns={cluster_cols[0]: "Cluster"}, inplace=True)

# ============================================================
# 3. FILTROS (Cluster, Máquina, Shift, EQ Type)
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

# Filtrar original
df_filt = df_original.copy()

if shift_sel != "Todos":
    df_filt = df_filt[df_filt["Shift"] == shift_sel]

if eq_sel != "Todos":
    df_filt = df_filt[df_filt["EQ Type"] == eq_sel]

# ============================================================
# 4. MANTENIMIENTO RECOMENDADO (DE LA TABLA FINAL)
# ============================================================

try:
    rec_days = float(df_final["Maintenance_Recommended"].mean())
    st.success(f"🟢 Se recomienda mantenimiento en **{round(rec_days,1)} días**.")
except:
    st.warning("No se pudo calcular el mantenimiento recomendado.")

# ============================================================
# 5. GRÁFICO: HISTÓRICO Y PREDICCIÓN POR MÁQUINA (TSB & Croston)
# ============================================================

st.subheader(f"📉 Tendencia histórica y predicción (TSB & Croston) – Máquina: {machine_sel}")

df_machine = df_filt[df_filt["Machine Name"] == machine_sel].copy()

# Asegurar que esté ordenado
df_machine = df_machine.sort_values("Date")

# Extraer predicciones desde tabla final
try:
    row = df_final[df_final["Machine"] == machine_sel].iloc[0]
    pred_tsb = row["Weekly_Prediction"]
    pred_cros = row["Weekly_Prediction"]  # si tienes columna aparte cámbiala aquí
except:
    pred_tsb = None
    pred_cros = None

fig_m = go.Figure()

# Línea histórica
fig_m.add_trace(go.Scatter(
    x=df_machine["Date"],
    y=df_machine["Failures"],
    mode="lines+markers",
    name="Histórico",
    line=dict(color="#00e5ff")
))

# Punto predicción Croston
if pred_cros is not None:
    fig_m.add_trace(go.Scatter(
        x=[df_machine["Date"].max() + pd.Timedelta(days=7)],
        y=[pred_cros],
        mode="markers",
        name="Predicción Croston",
        marker=dict(color="magenta", size=12)
    ))

# Punto predicción TSB
if pred_tsb is not None:
    fig_m.add_trace(go.Scatter(
        x=[df_machine["Date"].max() + pd.Timedelta(days=7)],
        y=[pred_tsb],
        mode="markers",
        name="Predicción TSB",
        marker=dict(color="yellow", size=12)
    ))

fig_m.update_layout(height=350, xaxis_title="Fecha", yaxis_title="Fallas estimadas")
st.plotly_chart(fig_m, use_container_width=True)

# ============================================================
# 6. GRÁFICO: HISTÓRICO Y PREDICCIÓN POR CLÚSTER
# ============================================================

st.subheader(f"📊 Tendencia histórica y predicción por CLÚSTER – {cluster_sel}")

df_cluster = df_filt[df_filt["Cluster"] == cluster_sel].copy()
df_cluster = df_cluster.sort_values("Date")

# Promedio de fallas por clúster por semana
df_cluster_grouped = df_cluster.groupby("Date")["Failures"].mean()

fig_c = go.Figure()

# Línea histórica
fig_c.add_trace(go.Scatter(
    x=df_cluster_grouped.index,
    y=df_cluster_grouped.values,
    mode="lines+markers",
    name="Histórico Cluster",
    line=dict(color="orange")
))

# Predicción cluster (promedio de predicciones individuales)
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

fig_c.update_layout(height=350, xaxis_title="Fecha", yaxis_title="Fallas estimadas")
st.plotly_chart(fig_c, use_container_width=True)

# ============================================================
# 7. MÉTRICAS DEL MODELO (MAE / RMSE / MASE)
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

# ============================================================
# FIN DEL ARCHIVO
# ============================================================
