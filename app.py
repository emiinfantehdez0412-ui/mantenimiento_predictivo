import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go

# ===============================
# CONFIG
# ===============================
st.set_page_config(page_title="FLEX Predictivo", layout="wide")

st.markdown(
    """
    <h1 style='text-align:center; color:#4DA3FF;'>🛠️ Dashboard de Mantenimiento Predictivo FLEX</h1>
    """,
    unsafe_allow_html=True
)

# ===============================
# LOAD DATA
# ===============================
@st.cache_data
def load_data():
    df_final = pd.read_excel("final_table_FIXED.xlsx")
    df_events = pd.read_excel("Mantenimiento_FLEX.xlsx")
    return df_final, df_events

df_final, df_events = load_data()

# ===============================
# SIDEBAR
# ===============================
with st.sidebar:
    st.header("🔍 Filtros")
    machines = df_final["Machine"].unique()
    clusters = df_final["Cluster_Name"].unique()

    machine_selected = st.selectbox("Selecciona una máquina:", machines)
    cluster_selected = st.selectbox("Selecciona un clúster:", clusters)

# ===============================
# CARDS FUNCTION
# ===============================
def metric_card(title, value, color="#2E86C1"):
    st.markdown(
        f"""
        <div style="
            background-color:{color};
            padding:15px;
            border-radius:10px;
            color:white;
            text-align:center;
            font-size:18px;">
            <b>{title}</b><br>
            <span style="font-size:26px;">{value}</span>
        </div>
        """,
        unsafe_allow_html=True
    )


# ===============================
# TABS LAYOUT
# ===============================
tab1, tab2, tab3, tab4 = st.tabs([
    "📌 Máquina",
    "🏭 Clúster",
    "🤖 EQ Type",
    "📊 Tabla"
])

# ===============================
# TAB 1 — MACHINE VIEW
# ===============================
with tab1:
    st.markdown("## 📌 Información de la Máquina")

    m = df_final[df_final["Machine"] == machine_selected].iloc[0]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Failure Rate", round(m["Failure_Rate"], 4))
    with col2:
        metric_card("Avg Severity", round(m["Avg_Severity"], 4))
    with col3:
        metric_card("Total Downtime", round(m["Total_Downtime"], 2))
    with col4:
        metric_card("Número de Fallas", int(m["Num_Failures"]))

    st.markdown("---")

    # HISTORICAL TREND
    # ======================================
# HISTORICAL + FORECASTED FAILURES (MACHINE)
# ======================================

st.markdown("### 📈 Tendencia Histórica y Predicción de Fallas (Máquina)")

machine_hist = df_events[df_events["Machine Name"] == machine_selected].copy()

# Convertir fecha
machine_hist["Date"] = pd.to_datetime(machine_hist["Date"])

# Agrupar por mes (YYYY-MM)
machine_hist["YearMonth"] = machine_hist["Date"].dt.to_period("M").astype(str)

# Contar fallas
failures_by_month = (
    machine_hist.groupby("YearMonth")
    .size()
    .reset_index(name="Failures")
)

# Forecast individual de la máquina
forecast_value = m["Weekly_Prediction"]

# Fecha futura (1 semana después del último evento)
future_date = (machine_hist["Date"].max() + pd.DateOffset(weeks=1)).strftime("%Y-%m")

forecast_df_machine = pd.DataFrame({
    "YearMonth": [future_date],
    "Failures": [forecast_value]
})

# =================== GRÁFICA ===================
fig_m = go.Figure()

# Históricas
fig_m.add_trace(go.Scatter(
    x=failures_by_month["YearMonth"],
    y=failures_by_month["Failures"],
    mode="lines+markers",
    name="Fallas históricas",
    line=dict(color="#4DA3FF", width=3),
    marker=dict(size=7)
))

# Forecast
fig_m.add_trace(go.Scatter(
    x=[future_date],
    y=[forecast_value],
    mode="markers+text",
    name="Predicción semanal",
    marker=dict(color="#FF8C00", size=12),
    text=["Forecast"],
    textposition="top center"
))

fig_m.update_layout(
    title=f"Fallas Históricas + Predicción – {machine_selected}",
    xaxis_title="Mes",
    yaxis_title="Número de fallas",
    template="plotly_white"
)

st.plotly_chart(fig_m, use_container_width=True)

# ======================================
# HISTORICAL + FORECASTED FAILURES (CLUSTER)
# ======================================

st.markdown("### 📈 Tendencia Histórica y Predicción de Fallas (Clúster)")

# Todas las máquinas del cluster
cluster_machines = cluster_df["Machine"].unique()

cluster_events = df_events[df_events["Machine Name"].isin(cluster_machines)].copy()

# Convertir fecha
cluster_events["Date"] = pd.to_datetime(cluster_events["Date"])

# Agrupar por mes
cluster_events["YearMonth"] = cluster_events["Date"].dt.to_period("M").astype(str)

# Contar fallas totales por mes
cluster_failures_by_month = (
    cluster_events.groupby("YearMonth")
    .size()
    .reset_index(name="Failures")
)

# Forecast cluster = suma de forecasts de sus máquinas
cluster_forecast_value = cluster_df["Weekly_Prediction"].sum()

# Fecha futura
future_date_cluster = (
    cluster_events["Date"].max() + pd.DateOffset(weeks=1)
).strftime("%Y-%m")

forecast_df_cluster = pd.DataFrame({
    "YearMonth": [future_date_cluster],
    "Failures": [cluster_forecast_value]
})

# =================== GRÁFICA ===================
fig_c = go.Figure()

# Históricas cluster
fig_c.add_trace(go.Scatter(
    x=cluster_failures_by_month["YearMonth"],
    y=cluster_failures_by_month["Failures"],
    mode="lines+markers",
    name="Fallas históricas (Cluster)",
    line=dict(color="#008080", width=3),
    marker=dict(size=7)
))

# Forecast cluster
fig_c.add_trace(go.Scatter(
    x=[future_date_cluster],
    y=[cluster_forecast_value],
    mode="markers+text",
    name="Predicción semanal total",
    marker=dict(color="#FF4500", size=12),
    text=["Forecast"],
    textposition="top center"
))

fig_c.update_layout(
    title=f"Fallas Históricas + Predicción – {cluster_selected}",
    xaxis_title="Mes",
    yaxis_title="Número total de fallas",
    template="plotly_white"
)

st.plotly_chart(fig_c, use_container_width=True)


# ===============================
# TAB 2 — CLUSTER VIEW
# ===============================
with tab2:
    st.markdown(f"## 🏭 Máquinas en: **{cluster_selected}**")

    cluster_df = df_final[df_final["Cluster_Name"] == cluster_selected]

    fig2 = px.bar(
        cluster_df,
        x="Machine",
        y="Num_Failures",
        title="Fallos por Máquina",
        color="Num_Failures",
        color_continuous_scale="Blues"
    )
    fig2.update_layout(template="plotly_white")
    st.plotly_chart(fig2, use_container_width=True)


# ===============================
# TAB 3 — EQ TYPE
# ===============================
with tab3:
    st.markdown("## 🤖 EQ Type que más falla")

    eq_fail = df_events.groupby("EQ Type")["Downtime"].count().reset_index()
    eq_fail = eq_fail.sort_values(by="Downtime", ascending=False)

    fig3 = px.bar(eq_fail, x="EQ Type", y="Downtime", color="Downtime",
                  color_continuous_scale="Tealgrn")
    fig3.update_layout(template="plotly_white")
    st.plotly_chart(fig3, use_container_width=True)

    top_eq = eq_fail.iloc[0]
    metric_card(f"EQ Type Más Crítico", f"{top_eq['EQ Type']} ({top_eq['Downtime']} fallas)", "#117864")


# ===============================
# TAB 4 — RAW TABLE
# ===============================
with tab4:
    st.markdown("## 📊 Tabla del Clúster Seleccionado")
    st.dataframe(cluster_df)
