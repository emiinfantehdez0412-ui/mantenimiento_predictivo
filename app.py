import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Dashboard Predictivo", layout="wide")

st.title("🔧 Dashboard de Mantenimiento Predictivo")

# -------------------------------------------------------------
# 1. SUBIDA DE ARCHIVOS
# -------------------------------------------------------------
st.sidebar.header("📂 Carga de archivos")

orig_file = st.sidebar.file_uploader("Sube la base ORIGINAL (Mantenimiento FLEX.xlsx)", type=["xlsx"])
proc_file = st.sidebar.file_uploader("Sube la tabla PROCESADA (final_table.xlsx)", type=["xlsx"])

if orig_file:
    df_orig = pd.read_excel(orig_file)
    st.sidebar.success("Base original cargada correctamente. ✔")

if proc_file:
    df_proc = pd.read_excel(proc_file)
    st.sidebar.success("Tabla procesada cargada correctamente. ✔")


# NO CONTINUAR SI NO HAY AMBAS BASES
if not orig_file or not proc_file:
    st.warning("Por favor sube **ambos archivos** para continuar.")
    st.stop()

# -------------------------------------------------------------
# 2. LIMPIEZA BASE ORIGINAL
# -------------------------------------------------------------
df_orig['Date'] = pd.to_datetime(df_orig['Date'])
df_orig['Downtime'] = df_orig['Downtime'].fillna(0)

# -------------------------------------------------------------
# 3. FILTROS
# -------------------------------------------------------------
st.sidebar.header("🎛 Filtros")

cluster_opt = st.sidebar.selectbox("Selecciona un clúster:", sorted(df_proc["Cluster"].unique()))
machines_cluster = df_proc[df_proc["Cluster"] == cluster_opt]["Machine"].unique()

machine_opt = st.sidebar.selectbox("Selecciona una máquina:", machines_cluster)

# FILTROS ADICIONALES DEL HISTÓRICO
shifts = sorted(df_orig["Shift"].dropna().unique())
shift_opt = st.sidebar.selectbox("Selecciona turno (Shift):", ["Todos"] + list(shifts))

eqtypes = sorted(df_orig["EQ Type"].dropna().unique())
eq_opt = st.sidebar.selectbox("Selecciona EQ Type:", ["Todos"] + list(eqtypes))

# -------------------------------------------------------------
# 4. INFORMACIÓN DE LA MÁQUINA (TABLA PROCESADA)
# -------------------------------------------------------------
machine_row = df_proc[df_proc["Machine"] == machine_opt].iloc[0]

maintenance_days = machine_row["Maintenance_Recommended"]
tsb_pred = machine_row["Weekly_Prediction"]
mae_c = machine_row["MAE_Croston"]
mae_t = machine_row["MAE_TSB"]
best_model = machine_row["Best_Model"]
best_mae = machine_row["Best_MAE"]

# -------------------------------------------------------------
# 5. MANTENIMIENTO RECOMENDADO
# -------------------------------------------------------------
st.header("🛠️ Mantenimiento recomendado")

st.success(f"✔ Se recomienda mantenimiento en **{maintenance_days}**.")

# -------------------------------------------------------------
# 6. HISTÓRICO SEMANAL + PREDICCIÓN
# -------------------------------------------------------------
st.header("📉 Tendencia semanal histórica y predicción (TSB & Croston)")

df_m = df_orig[df_orig["Machine Name"] == machine_opt].copy()

# Aplicar filtros
if shift_opt != "Todos":
    df_m = df_m[df_m["Shift"] == shift_opt]

if eq_opt != "Todos":
    df_m = df_m[df_m["EQ Type"] == eq_opt]

# Agrupación semanal
df_m["week"] = df_m["Date"].dt.to_period("W").apply(lambda r: r.start_time)
weekly = df_m.groupby("week")["Downtime"].sum().reset_index()

if len(weekly) == 0:
    st.warning("⚠ No hay datos suficientes para graficar el historial.")
else:

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=weekly["week"],
        y=weekly["Downtime"],
        mode='lines+markers',
        name='Histórico',
        line=dict(color="cyan")
    ))

    # Línea de predicción
    fig.add_trace(go.Scatter(
        x=[weekly["week"].max() + pd.Timedelta(days=7)],
        y=[tsb_pred],
        mode='markers',
        name='Predicción TSB',
        marker=dict(color="yellow", size=12)
    ))

    fig.update_layout(
        title=f"Predicción TSB – {machine_opt}",
        xaxis_title="Semana",
        yaxis_title="Fallas estimadas",
        template="plotly_dark"
    )

    st.plotly_chart(fig, use_container_width=True)

# -------------------------------------------------------------
# 7. MÉTRICAS DE ERROR
# -------------------------------------------------------------
st.header("📊 Métricas de error del modelo (MAE)")

col1, col2, col3, col4 = st.columns(4)

col1.metric("MAE Croston", f"{mae_c:.6f}")
col2.metric("MAE TSB", f"{mae_t:.6f}")
col3.metric("Mejor Modelo", best_model)
col4.metric("MAE del Mejor Modelo", f"{best_mae:.6f}")

st.info("Dashboard generado correctamente. ✔")
