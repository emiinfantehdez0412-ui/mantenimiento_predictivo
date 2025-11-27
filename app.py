import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ==========================================================
# CONFIGURACIÓN GENERAL
# ==========================================================
st.set_page_config(
    page_title="Dashboard de Mantenimiento Predictivo",
    layout="wide",
    page_icon="🛠️"
)

st.title("🔧 Dashboard de Mantenimiento Predictivo")
st.write("Predicciones basadas en clustering + TSB para fallas semanales.")

# ==========================================================
# 1. CARGA DE ARCHIVOS
# ==========================================================
st.sidebar.header("📂 Carga de archivos")

file_original = st.sidebar.file_uploader(
    "Sube la base ORIGINAL (Mantenimiento FLEX.xlsx)", type=["xlsx"]
)

file_processed = st.sidebar.file_uploader(
    "Sube la tabla PROCESADA (final_table.xlsx)", type=["xlsx"]
)

df_original = None
df_processed = None

if file_original:
    df_original = pd.read_excel(file_original)
    st.sidebar.success("Base original cargada correctamente. ✔")

if file_processed:
    df_processed = pd.read_excel(file_processed)
    st.sidebar.success("Tabla procesada cargada correctamente. ✔")

# ==========================================================
# VALIDACIÓN DEL ARCHIVO PROCESADO
# ==========================================================
if df_processed is None:
    st.warning("⚠️ Debes subir la **tabla procesada** final_table.xlsx")
    st.stop()

required_columns = [
    "Machine", "Cluster", "Cluster_Name",
    "Avg_TBF", "Maintenance_Recommended",
    "Weekly_Prediction",
    "MAE_Croston", "MAE_TSB",
    "Best_Model", "Best_MAE"
]

missing = [col for col in required_columns if col not in df_processed.columns]

if missing:
    st.error(f"La tabla procesada NO contiene las columnas requeridas: {missing}")
    st.stop()

# ==========================================================
# 2. FILTROS
# ==========================================================
st.sidebar.subheader("🔎 Selección de clúster y máquina")

clusters = sorted(df_processed["Cluster"].unique())
selected_cluster = st.sidebar.selectbox("Selecciona un clúster:", clusters)

filtered_df = df_processed[df_processed["Cluster"] == selected_cluster]

machines = sorted(filtered_df["Machine"].unique())
selected_machine = st.sidebar.selectbox("Selecciona una máquina:", machines)

machine_row = filtered_df[filtered_df["Machine"] == selected_machine].iloc[0]

# ==========================================================
# 3. MANTENIMIENTO RECOMENDADO
# ==========================================================
st.header("🛠️ Mantenimiento recomendado")

maintenance = machine_row["Maintenance_Recommended"]

if pd.isna(maintenance):
    st.warning("⚠️ No hay información suficiente para calcular el mantenimiento recomendado.")
else:
    st.success(f"✔ Se recomienda mantenimiento en **{maintenance}**.")

# ==========================================================
# 4. GRÁFICO TSB (Tendencia semanal)
# ==========================================================
st.header("📉 Tendencia semanal histórica y predicción (TSB)")

if "Weekly_Prediction" not in df_processed.columns:
    st.warning("⚠️ La columna 'Weekly_Prediction' no se encuentra en la tabla procesada.")
else:
    pred = machine_row["Weekly_Prediction"]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=["Semana siguiente"],
        y=[pred],
        name="Predicción TSB",
        marker_color="#00bcd4"
    ))

    fig.update_layout(
        title=f"Predicción TSB – {selected_machine}",
        yaxis_title="Fallas estimadas",
        template="plotly_dark"
    )

    st.plotly_chart(fig, use_container_width=True)

# ==========================================================
# 5. MÉTRICAS DE ERROR
# ==========================================================
st.header("📊 Métricas de error del modelo (MAE)")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("MAE Croston", f"{machine_row['MAE_Croston']:.6f}")

with col2:
    st.metric("MAE TSB", f"{machine_row['MAE_TSB']:.6f}")

with col3:
    st.metric("Mejor Modelo", machine_row["Best_Model"])

with col4:
    st.metric("MAE del Mejor Modelo", f"{machine_row['Best_MAE']:.6f}")

# ==========================================================
# FIN DEL DASHBOARD
# ==========================================================
st.info("Dashboard generado correctamente. ✔")
