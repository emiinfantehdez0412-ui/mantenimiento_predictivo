import streamlit as st
import pandas as pd
import plotly.express as px

# =====================================================================
# PAGE CONFIG
# =====================================================================

st.set_page_config(
    page_title="Dashboard FLEX – Mantenimiento Predictivo",
    layout="wide"
)

st.title("🛠️ Dashboard de Mantenimiento Predictivo – FLEX")


# =====================================================================
# LOAD DATA
# =====================================================================

@st.cache_data
def load_data():
    df_final = pd.read_excel("final_table_FIXED.xlsx")
    df_events = pd.read_excel("Mantenimiento_FLEX.xlsx")
    df_raw = pd.read_csv("historical_failures.csv")  # si no la tienes la quitamos
    return df_final, df_events, df_raw

df_final, df_events, df_raw = load_data()


# =====================================================================
# SIDEBAR FILTERS
# =====================================================================

st.sidebar.header("Filtros")

machines = df_final["Machine"].unique()
clusters = df_final["Cluster_Name"].unique()

machine_selected = st.sidebar.selectbox("Selecciona una máquina:", machines)
cluster_selected = st.sidebar.selectbox("Selecciona un clúster:", clusters)


# =====================================================================
# MACHINE SUMMARY
# =====================================================================

st.subheader(f"📍 Resumen de: **{machine_selected}**")

m = df_final[df_final["Machine"] == machine_selected].iloc[0]

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Failure Rate", round(m["Failure_Rate"], 4))

with col2:
    st.metric("Avg Severity", round(m["Avg_Severity"], 4))

with col3:
    st.metric("Total Downtime", round(m["Total_Downtime"], 2))

with col4:
    st.metric("Número de Fallas", int(m["Num_Failures"]))


# =====================================================================
# HISTORICAL TREND (BY MACHINE)
# =====================================================================

st.subheader("📈 Tendencia Histórica – Downtime por Máquina")

machine_hist = df_events[df_events["Machine Name"] == machine_selected]

if machine_hist.empty:
    st.warning("No hay datos históricos para esta máquina.")
else:
    fig = px.line(
        machine_hist,
        x="Date",
        y="Downtime",
        title=f"Tendencia de Downtime – {machine_selected}"
    )
    st.plotly_chart(fig, use_container_width=True)


# =====================================================================
# PREDICTION – MACHINE LEVEL
# =====================================================================

st.markdown("### 🔮 Predicción y Mantenimiento Recomendado")

col1, col2 = st.columns(2)

with col1:
    st.metric("Weekly Prediction", round(m["Weekly_Prediction"], 3))

with col2:
    st.success(f"Mantenimiento Recomendado: **{m['Maintenance_Recommended']}**")


# =====================================================================
# MODEL METRICS
# =====================================================================

st.subheader("📊 Métricas del Modelo (Mejor Modelo Seleccionado)")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Modelo", m["Best_Model"])

with col2:
    st.metric("Best MAE", round(m["Best_MAE"], 5))

with col3:
    st.metric("Predicción Final", round(m["Best_Prediction"], 5))


# =====================================================================
# CLUSTER ANALYSIS
# =====================================================================

st.subheader(f"🏭 Análisis por Clúster – {cluster_selected}")

cluster_df = df_final[df_final["Cluster_Name"] == cluster_selected]

fig2 = px.bar(
    cluster_df,
    x="Machine",
    y="Num_Failures",
    title=f"Fallos por Máquina en el Clúster {cluster_selected}",
)
st.plotly_chart(fig2, use_container_width=True)


# =====================================================================
# EQ TYPE THAT FAILS THE MOST
# =====================================================================

st.subheader("🤖 EQ Type que más falla")

eq_fail = df_events.groupby("EQ Type")["Downtime"].count().reset_index()
eq_fail = eq_fail.sort_values(by="Downtime", ascending=False)

fig3 = px.bar(
    eq_fail,
    x="EQ Type",
    y="Downtime",
    title="Fallas por Tipo de Equipo (EQ Type)"
)
st.plotly_chart(fig3, use_container_width=True)

top_eq = eq_fail.iloc[0]

st.warning(
    f"**El EQ Type que MÁS falla es:** `{top_eq['EQ Type']}` "
    f"con **{top_eq['Downtime']}** fallas."
)


# =====================================================================
# TABLE OF THE SELECTED CLUSTER
# =====================================================================

st.subheader("📘 Tabla Completa del Clúster Seleccionado")

st.dataframe(cluster_df[
    [
        "Machine",
        "Failure_Rate",
        "Num_Failures",
        "Weekly_Prediction",
        "Maintenance_Recommended",
        "Best_Model",
        "Best_MAE"
    ]
])


# =====================================================================
# RAW HISTORICAL TABLE (OPTIONAL)
# =====================================================================

st.subheader("📄 Datos Históricos (Raw)")

with st.expander("Mostrar/Ocultar"):
    st.dataframe(df_raw)
