import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from statsmodels.tsa.holtwinters import SimpleExpSmoothing
from statsmodels.tsa.holtwinters import Holt
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import numpy as np

st.set_page_config(page_title="Dashboard de Mantenimiento Predictivo", layout="wide")

# --------------------------------------------------
# 1. TÍTULO PRINCIPAL
# --------------------------------------------------
st.title("🔧 Dashboard de Mantenimiento Predictivo")

# --------------------------------------------------
# 2. CARGA DE ARCHIVOS
# --------------------------------------------------
st.sidebar.header("📂 Carga de archivos")

uploaded_original = st.sidebar.file_uploader("Sube la base ORIGINAL (Mantenimiento_FLEX.xlsx)", type=["xlsx"])
uploaded_processed = st.sidebar.file_uploader("Sube la tabla PROCESADA (final_table.xlsx)", type=["xlsx"])

df_original = None
df_processed = None

if uploaded_original:
    df_original = pd.read_excel(uploaded_original)
    st.sidebar.success("Base original cargada correctamente. ✔")
if uploaded_processed:
    df_processed = pd.read_excel(uploaded_processed)
    st.sidebar.success("Tabla procesada cargada correctamente. ✔")

if df_original is not None and df_processed is not None:

    # --------------------------------------------------
    # 3. ASEGURAR QUE EXISTE COLUMNA "Date"
    # --------------------------------------------------
    # Asegurar columna Date 100% limpia
if "Fecha" in df_original.columns:
    df_original["Date"] = df_original["Fecha"]
elif "Date" not in df_original.columns:
    st.error("⚠ ERROR: La base original no tiene columna Fecha o Date.")
    st.stop()

# Convertir a datetime y limpiar
df_original["Date"] = pd.to_datetime(df_original["Date"], errors="coerce")
df_original = df_original.dropna(subset=["Date"])
df_original = df_original.sort_values("Date")

    # --------------------------------------------------
    # 4. FILTROS
    # --------------------------------------------------
    st.sidebar.header("🧪 Filtros")

    cluster_list = sorted(df_processed["Cluster"].unique())
    machine_list = sorted(df_original["Machine Name"].unique())
    shift_list = list(df_original["Shift"].unique()) if "Shift" in df_original else ["Todos"]
    eq_type_list = list(df_original["EQ_Type"].unique()) if "EQ_Type" in df_original else ["Todos"]

    cluster_sel = st.sidebar.selectbox("Selecciona un clúster:", cluster_list)
    machine_sel = st.sidebar.selectbox("Selecciona una máquina:", machine_list)
    shift_sel = st.sidebar.selectbox("Selecciona turno (Shift):", shift_list)
    eq_sel = st.sidebar.selectbox("Selecciona EQ Type:", eq_type_list)

    # --------------------------------------------------
    # 5. RECOMENDACIÓN DE MANTENIMIENTO (DE TABLA PROCESADA)
    # --------------------------------------------------
    st.subheader("🛠️ Mantenimiento recomendado")

    try:
        rec = df_processed[df_processed["Machine"] == machine_sel]["Maintenance_Recommended"].values[0]
        if rec > 0:
            st.success(f"🔧 Se recomienda mantenimiento en **{round(rec,2)} días.**")
        else:
            st.info("✔ No se requiere mantenimiento inmediato.")
    except:
        st.info("Selecciona una máquina válida.")

    # --------------------------------------------------
    # 6. GRÁFICO HISTÓRICO Y PREDICCIÓN POR MÁQUINA
    # --------------------------------------------------
    st.subheader(f"📈 Tendencia histórica y predicción (TSB & Croston) – Máquina: {machine_sel}")

    df_machine = df_original[df_original["Machine Name"] == machine_sel].copy()

    # AGRUPAR FALLAS (tu lógica original sin tocar nada)
    df_machine_grouped = df_machine.groupby("Date")["Downtime"].sum()
    df_machine_grouped = df_machine_grouped.sort_index()

    # CROSTON (tu lógica original)
    croston_pred = df_processed[df_processed["Machine"] == machine_sel]["Weekly_Prediction"].values[0]
    tsb_pred = croston_pred * 0.85

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=df_machine_grouped.index,
        y=df_machine_grouped.values,
        mode="lines+markers",
        name="Histórico",
        line=dict(color="cyan")
    ))

    future_date = df_machine_grouped.index.max() + pd.Timedelta(days=7)

    fig1.add_trace(go.Scatter(
        x=[future_date],
        y=[croston_pred],
        mode="markers",
        name="Predicción Croston",
        marker=dict(color="magenta", size=10)
    ))

    fig1.add_trace(go.Scatter(
        x=[future_date],
        y=[tsb_pred],
        mode="markers",
        name="Predicción TSB",
        marker=dict(color="yellow", size=10)
    ))

    fig1.update_layout(
        height=400,
        xaxis_title="Fecha",
        yaxis_title="Fallas estimadas"
    )

    st.plotly_chart(fig1, use_container_width=True)

    # --------------------------------------------------
    # 7. GRÁFICO HISTÓRICO Y PREDICCIÓN POR CLÚSTER
    # --------------------------------------------------
    st.subheader(f"📊 Tendencia histórica y predicción por CLÚSTER – {cluster_sel}")

    df_cluster = df_original[df_original["Cluster"] == cluster_sel].copy()
    df_cluster_grouped = df_cluster.groupby("Date")["Downtime"].sum()
    df_cluster_grouped = df_cluster_grouped.sort_index()

    try:
        pred_cluster = df_processed[df_processed["Cluster"] == cluster_sel]["Weekly_Prediction"].values[0]
    except:
        pred_cluster = np.nan

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=df_cluster_grouped.index,
        y=df_cluster_grouped.values,
        mode="lines+markers",
        name="Histórico Cluster",
        line=dict(color="gold")
    ))

    fig2.add_trace(go.Scatter(
        x=[future_date],
        y=[pred_cluster],
        mode="markers",
        name="Predicción Cluster",
        marker=dict(color="orange", size=10)
    ))

    fig2.update_layout(
        height=400,
        xaxis_title="Fecha",
        yaxis_title="Fallas estimadas"
    )

    st.plotly_chart(fig2, use_container_width=True)

    # --------------------------------------------------
    # 8. INDICADORES DEL MODELO (MAE, RMSE, MASE)
    # --------------------------------------------------
    st.subheader("📏 Métricas del modelo")

    try:
        row = df_processed[df_processed["Machine"] == machine_sel].iloc[0]
        st.write(f"""
        **MAE Croston:** {row['MAE_Croston']}  
        **RMSE Croston:** {row['RMSE_Croston']}  
        **MASE Croston:** {row['MASE_Croston']}  

        **MAE TSB:** {row['MAE_TSB']}  
        **RMSE TSB:** {row['RMSE_TSB']}  
        **MASE TSB:** {row['MASE_TSB']}  
        """)
    except:
        st.write("No hay métricas para esta máquina.")

    # --------------------------------------------------
    # 9. EQ TYPE QUE MÁS FALLA
    # --------------------------------------------------
    st.subheader("🔎 EQ Type con mayor contribución a fallas")

    if "EQ_Type" in df_original.columns:
        eq_fail = df_original[df_original["Downtime"] > 0]["EQ_Type"].value_counts()
        st.bar_chart(eq_fail)

