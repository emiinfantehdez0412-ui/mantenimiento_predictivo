import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
from statsmodels.tsa.holtwinters import ExponentialSmoothing


# ============================================================
#                       CONFIGURACIÓN
# ============================================================
st.set_page_config(page_title="Dashboard de Mantenimiento Predictivo",
                   layout="wide",
                   initial_sidebar_state="expanded")

st.title("🛠️ Dashboard de Mantenimiento Predictivo")


# ============================================================
#                 SUBIR ARCHIVOS
# ============================================================
st.sidebar.header("📂 Carga de archivos")

file_original = st.sidebar.file_uploader("Sube la base ORIGINAL (Mantenimiento_FLEX.xlsx)", type=["xlsx"])
file_final = st.sidebar.file_uploader("Sube la tabla PROCESADA (final_table.xlsx)", type=["xlsx"])

if file_original is None or file_final is None:
    st.warning("Sube ambos archivos para comenzar.")
    st.stop()

df_original = pd.read_excel(file_original)
final = pd.read_excel(file_final)

st.sidebar.success("Base original cargada correctamente. ✔")
st.sidebar.success("Tabla procesada cargada correctamente. ✔")


# ============================================================
#              NORMALIZAR NOMBRES DE COLUMNAS
# ============================================================
df_original.columns = df_original.columns.str.strip()
final.columns = final.columns.str.strip()

if "Machine Name" not in df_original.columns:
    st.error("❌ La base ORIGINAL debe contener la columna 'Machine Name'.")
    st.stop()

if "Machine" not in final.columns or "Cluster" not in final.columns:
    st.error("❌ La tabla procesada debe contener 'Machine' y 'Cluster'.")
    st.stop()


# ============================================================
#                        FILTROS
# ============================================================
st.sidebar.header("🎛️ Filtros")

clusters = sorted(final["Cluster"].unique())
cluster_sel = st.sidebar.selectbox("Selecciona un clúster:", clusters)

machines_cluster = sorted(final[final["Cluster"] == cluster_sel]["Machine"].unique())
machine_sel = st.sidebar.selectbox("Selecciona una máquina:", machines_cluster)

shifts = ["Todos"] + sorted(df_original["Shift"].astype(str).unique())
shift_sel = st.sidebar.selectbox("Selecciona turno (Shift):", shifts)

eqtypes = ["Todos"] + sorted(df_original["EQ Type"].astype(str).unique())
eq_sel = st.sidebar.selectbox("Selecciona EQ Type:", eqtypes)


# ============================================================
#            FILTRADO POR CLUSTER Y MÁQUINA
# ============================================================

df_cluster = df_original[df_original["Machine Name"].isin(machines_cluster)].copy()
df_machine = df_original[df_original["Machine Name"] == machine_sel].copy()

if shift_sel != "Todos":
    df_machine = df_machine[df_machine["Shift"].astype(str) == shift_sel]

if eq_sel != "Todos":
    df_machine = df_machine[df_machine["EQ Type"].astype(str) == eq_sel]


# ============================================================
#                 HISTÓRICO + PREDICCIÓN
# ============================================================
def prepare_weekly_series(df):
    df2 = df.copy()
    df2["Date"] = pd.to_datetime(df2["Date"], errors="coerce")
    df2 = df2.dropna(subset=["Date"])
    df2["Week"] = df2["Date"].dt.to_period("W").dt.start_time
    weekly = df2.groupby("Week")["Downtime"].count()
    return weekly


def croston_forecast(series):
    if len(series) < 2:
        return 0

    freq = series.replace(0, np.nan).dropna()
    alpha = 0.3

    intervals = freq.index.to_series().diff().dt.days.fillna(0)
    if len(intervals) > 1:
        avg_interval = intervals.mean() / 7
    else:
        avg_interval = 1

    estimate = alpha * freq.iloc[-1] + (1 - alpha) * freq.mean()
    return 1 / avg_interval if avg_interval != 0 else estimate


def tsb_forecast(series):
    if len(series) < 2:
        return 0
    model = ExponentialSmoothing(series, trend=None, seasonal=None)
    fit = model.fit()
    return fit.forecast(1).iloc[0]


# ============================================================
#                GRÁFICO HISTÓRICO POR CLÚSTER
# ============================================================

st.header("📊 Tendencia histórica y predicción por CLÚSTER ↩")
weekly_cluster = prepare_weekly_series(df_cluster)

if len(weekly_cluster) == 0:
    st.warning("No hay datos históricos para este clúster.")
else:
    tsb_pred_c = tsb_forecast(weekly_cluster)
    croston_pred_c = croston_forecast(weekly_cluster)

    fig_c = go.Figure()
    fig_c.add_trace(go.Scatter(x=weekly_cluster.index, y=weekly_cluster.values,
                               mode='lines+markers', name='Histórico', line=dict(color='cyan')))
    fig_c.add_trace(go.Scatter(x=[weekly_cluster.index[-1] + pd.Timedelta(weeks=1)],
                               y=[tsb_pred_c], mode='markers', name='Predicción TSB',
                               marker=dict(color='yellow', size=12)))
    fig_c.add_trace(go.Scatter(x=[weekly_cluster.index[-1] + pd.Timedelta(weeks=1)],
                               y=[croston_pred_c], mode='markers', name='Predicción Croston',
                               marker=dict(color='magenta', size=12)))

    st.plotly_chart(fig_c, use_container_width=True)


# ============================================================
#                GRÁFICO HISTÓRICO POR MÁQUINA
# ============================================================

st.header("📈 Tendencia histórica y predicción por MÁQUINA ↩")

weekly_machine = prepare_weekly_series(df_machine)

if len(weekly_machine) == 0:
    st.warning("No hay datos históricos para esta máquina.")
else:
    tsb_pred_m = tsb_forecast(weekly_machine)
    croston_pred_m = croston_forecast(weekly_machine)

    fig_m = go.Figure()
    fig_m.add_trace(go.Scatter(x=weekly_machine.index, y=weekly_machine.values,
                               mode='lines+markers', name='Histórico', line=dict(color='cyan')))

    fig_m.add_trace(go.Scatter(x=[weekly_machine.index[-1] + pd.Timedelta(weeks=1)],
                               y=[tsb_pred_m], mode='markers', name='Predicción TSB',
                               marker=dict(color='yellow', size=12)))

    fig_m.add_trace(go.Scatter(x=[weekly_machine.index[-1] + pd.Timedelta(weeks=1)],
                               y=[croston_pred_m], mode='markers', name='Predicción Croston',
                               marker=dict(color='magenta', size=12)))

    st.plotly_chart(fig_m, use_container_width=True)


# ============================================================
#         ¿QUÉ EQ TYPE GENERA MÁS FALLAS?
# ============================================================

st.header("🤖 EQ Type que genera más fallas")

if len(df_machine) == 0:
    st.info("No hay datos para esta máquina con los filtros seleccionados.")
else:
    eq_counts = df_machine["EQ Type"].value_counts()

    st.write("### EQ Types ordenados por número de fallas:")
    st.bar_chart(eq_counts)


# ============================================================
#            RECOMENDACIÓN DE MANTENIMIENTO
# ============================================================
st.header("🛠 Mantenimiento recomendado")

try:
    rec = final[final["Machine"] == machine_sel]["Maintenance_Recommended"].iloc[0]
    st.success(f"✔ Se recomienda mantenimiento en **{rec}**.")
except:
    st.info("No hay recomendación disponible para esta máquina en final_table.")
