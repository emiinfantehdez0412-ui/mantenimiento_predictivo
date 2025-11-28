import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

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

# Validar cluster
if df_original["Cluster"].isna().all():
    st.error("❌ ERROR: No se pudieron asignar los clusters a la base original. Revisa nombres.")
    st.stop()

# ============================================================
# 2. NORMALIZAR FECHAS
# ============================================================

if "Fecha" in df_original.columns:
    df_original.rename(columns={"Fecha": "Date"}, inplace=True)

if "Date" in df_original.columns:
    df_original["Date"] = pd.to_datetime(df_original["Date"], errors="coerce")

# Normalizar columna Cluster
cluster_cols = [c for c in df_original.columns if c.lower().strip() in ["cluster", "clúster", "clusters"]]
df_original.rename(columns={cluster_cols[0]: "Cluster"}, inplace=True)

# ============================================================
# 3. FILTROS
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

# Filtrar
df_filt = df_original.copy()

if shift_sel != "Todos":
    df_filt = df_filt[df_filt["Shift"] == shift_sel]

if eq_sel != "Todos":
    df_filt = df_filt[df_filt["EQ Type"] == eq_sel]

# ============================================================
# 4. MANTENIMIENTO RECOMENDADO
# ============================================================

try:
    rec_days = float(df_final["Maintenance_Recommended"].mean())
    st.success(f"🟢 Se recomienda mantenimiento en **{round(rec_days,1)} días**.")
except:
    st.warning("No se pudo calcular el mantenimiento recomendado.")

# ============================================================
# 5. GRÁFICO: HISTÓRICO Y PREDICCIÓN POR MÁQUINA
# ============================================================

st.subheader(f"📉 Tendencia histórica y predicción (TSB & Croston) – Máquina: {machine_sel}")

df_machine = df_filt[df_filt["Machine Name"] == machine_sel].copy()
df_machine = df_machine.sort_values("Date")

try:
    row = df_final[df_final["Machine"] == machine_sel].iloc[0]
    pred_tsb = row["Weekly_Prediction"]
    pred_cros = row["Weekly_Prediction"]
except:
    pred_tsb = None
    pred_cros = None

fig_m = go.Figure()
fig_m.add_trace(go.Scatter(
    x=df_machine["Date"],
    y=df_machine["Failures"],
    mode="lines+markers",
    name="Histórico",
    line=dict(color="#00e5ff")
))

if pred_cros is not None:
    fig_m.add_trace(go.Scatter(
        x=[df_machine["Date"].max() + pd.Timedelta(days=7)],
        y=[pred_cros],
        mode="markers",
        name="Predicción Croston",
        marker=dict(color="magenta", size=12)
    ))

if pred_tsb is not None:
    fig_m.add_trace(go.Scatter(
        x=[df_machine["Date"].max() + pd.Timedelta(days=7)],
        y=[pred_tsb],
        mode="markers",
        name="Predicción TSB",
        marker=dict(color="yellow", size=12)
    ))

fig_m.update_layout(height=350)
st.plotly_chart(fig_m, use_container_width=True)

# ============================================================
# 6. HISTÓRICO + PREDICCIONES POR CLÚSTER
# ============================================================

st.subheader(f"📊 Tendencia histórica y predicción por CLÚSTER – {cluster_sel}")

df_cluster = df_filt[df_filt["Cluster"] == cluster_sel].copy()
df_cluster = df_cluster.sort_values("Date")

df_cluster_grouped = df_cluster.groupby("Date")["Failures"].mean()

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

fig_c.update_layout(height=350)
st.plotly_chart(fig_c, use_container_width=True)

# ============================================================
# 7. MÉTRICAS (MAE)
# ============================================================

st.subheader("📐 Métricas del modelo")

try:
    row = df_final[df_final["Machine"] == machine_sel].iloc[0]
    col1, col2, col3 = st.columns(3)
    col1.metric("MAE Croston", round(row["MAE_Croston"], 3))
    col2.metric("MAE TSB", round(row["MAE_TSB"], 3))
    col3.metric("Mejor Modelo", "Croston" if row["MAE_Croston"] <= row["MAE_TSB"] else "TSB")
except:
    st.warning("No hay métricas para esta máquina.")

# ============================================================
# 8. 🔥 NUEVO: HEATMAP (TURNOS × EQ TYPE)
# ============================================================

st.subheader("🔥 Mapa de calor: Fallas por turno y EQ Type")

df_heat = df_filt.pivot_table(
    values="Failures",
    index="Shift",
    columns="EQ Type",
    aggfunc="sum",
    fill_value=0
)

fig_heat = px.imshow(
    df_heat,
    text_auto=True,
    color_continuous_scale="Inferno",
    aspect="auto",
)

st.plotly_chart(fig_heat, use_container_width=True)

# ============================================================
# 9. 📊 NUEVO: BARRAS POR EQ TYPE
# ============================================================

st.subheader("📊 Fallas promedio por EQ Type")

df_bar = df_filt.groupby("EQ Type")["Failures"].mean().reset_index()

fig_bar = px.bar(
    df_bar,
    x="EQ Type",
    y="Failures",
    color="EQ Type",
    text="Failures",
    title="Promedio de fallas por tipo de equipo"
)

st.plotly_chart(fig_bar, use_container_width=True)

# ============================================================
# 10. 🧾 NUEVO: TABLA INTERACTIVA
# ============================================================

st.subheader("📋 Tabla de datos filtrados")

st.dataframe(df_filt.sort_values("Date"), use_container_width=True)

# ============================================================
# 11. 💾 NUEVO: DESCARGA DE PREDICCIONES
# ============================================================

st.subheader("💾 Descargar predicciones")

export = df_final.to_excel("predicciones_export.xlsx", index=False)

with open("predicciones_export.xlsx", "rb") as f:
    st.download_button(
        label="Descargar Excel de Predicciones",
        data=f,
        file_name="predicciones_mantenimiento.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
