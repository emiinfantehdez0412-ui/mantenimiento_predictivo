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
# FIX: CONVERTIR Weekly_Prediction A NUMÉRICO
# ===============================
df_final["Weekly_Prediction"] = pd.to_numeric(
    df_final["Weekly_Prediction"], errors="coerce"
).fillna(0)

# Convertimos mantenimiento recomendado a string para evitar errores
df_final["Maintenance_Recommended"] = df_final["Maintenance_Recommended"].astype(str)

# ===========================================
# NORMALIZACIÓN DE PREDICCIONES PARA EL GAUGE
# ===========================================

# 1) Convertir a número real
df_final["Weekly_Prediction"] = pd.to_numeric(
    df_final["Weekly_Prediction"], errors="coerce"
).fillna(0)

# 2) Escalar predicciones para visualización
# (porque tus valores reales son como 1.2e-40 = invisibles)
df_final["Weekly_Pred_Scaled"] = df_final["Weekly_Prediction"] * 1_000_000_000_000

# ===============================
# SIDEBAR FILTERS – CASCADA + BADGE DE RIESGO
# ===============================

with st.sidebar:
    st.header("🔍 Filtros")

    clusters = df_final["Cluster_Name"].unique()
    cluster_selected = st.selectbox("Selecciona un clúster:", clusters)

    if "HIGH" in cluster_selected.upper():
        risk_color = "#E74C3C"
        risk_text = "🔴 HIGH RISK"
    else:
        risk_color = "#2ECC71"
        risk_text = "🟢 LOW RISK"

    st.markdown(
        f"""
        <div style="
            background-color:{risk_color};
            padding:10px;
            border-radius:8px;
            margin-bottom:15px;
            text-align:center;
            color:white;
            font-size:18px;
            font-weight:bold;">
            {risk_text}
        </div>
        """,
        unsafe_allow_html=True
    )

    filtered_machines = (
        df_final[df_final["Cluster_Name"] == cluster_selected]["Machine"].unique()
    )

    machine_selected = st.selectbox("Selecciona una máquina:", filtered_machines)

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
# TABS
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

# ===============================
# HISTORICAL + FORECAST (MACHINE)
# ===============================
st.markdown("### 📈 Tendencia Histórica y Predicción de Fallas (Máquina)")

machine_hist = df_events[df_events["Machine Name"] == machine_selected].copy()

if machine_hist.empty:
    st.warning("⚠️ No hay eventos de falla registrados para esta máquina.")
else:
    machine_hist["Date"] = pd.to_datetime(machine_hist["Date"])
    machine_hist["YearMonth"] = machine_hist["Date"].dt.to_period("M").astype(str)

    failures_by_month = (
        machine_hist.groupby("YearMonth").size().reset_index(name="Failures")
    )

    forecast_value = m["Weekly_Prediction"]
    future_date = (machine_hist["Date"].max() + pd.DateOffset(weeks=1)).strftime("%Y-%m")

    fig_m = go.Figure()

    fig_m.add_trace(go.Scatter(
        x=failures_by_month["YearMonth"],
        y=failures_by_month["Failures"],
        mode="lines+markers",
        name="Fallas históricas",
        line=dict(color="#4DA3FF")
    ))

    fig_m.add_trace(go.Scatter(
        x=[future_date],
        y=[forecast_value],
        mode="markers+text",
        text=["Forecast"],
        textposition="top center",
        name="Predicción",
        marker=dict(color="orange", size=12)
    ))

    st.plotly_chart(fig_m, use_container_width=True)

# ===============================
# HISTORICAL + FORECAST (CLUSTER)
# ===============================
st.markdown("### 📈 Tendencia Histórica y Predicción de Fallas (Clúster)")

cluster_df = df_final[df_final["Cluster_Name"] == cluster_selected]
cluster_machines = cluster_df["Machine"].unique()

cluster_events = df_events[df_events["Machine Name"].isin(cluster_machines)].copy()

if cluster_events.empty:
    st.warning("⚠️ No hay historial de fallas para este clúster.")
else:
    cluster_events["Date"] = pd.to_datetime(cluster_events["Date"])
    cluster_events["YearMonth"] = cluster_events["Date"].dt.to_period("M").astype(str)

    failures_cluster = (
        cluster_events.groupby("YearMonth").size().reset_index(name="Failures")
    )

    cluster_forecast = cluster_df["Weekly_Prediction"].sum()
    future_cluster_date = (cluster_events["Date"].max() + pd.DateOffset(weeks=1)).strftime("%Y-%m")

    fig_c = go.Figure()

    fig_c.add_trace(go.Scatter(
        x=failures_cluster["YearMonth"],
        y=failures_cluster["Failures"],
        mode="lines+markers",
        name="Fallas históricas",
        line=dict(color="#008080")
    ))

    fig_c.add_trace(go.Scatter(
        x=[future_cluster_date],
        y=[cluster_forecast],
        mode="markers+text",
        text=["Forecast"],
        textposition="top center",
        marker=dict(color="red", size=12)
    ))

    st.plotly_chart(fig_c, use_container_width=True)

# ===============================
# TAB 2 — CLUSTER VIEW
# ===============================
with tab2:
    st.markdown(f"## 🏭 Máquinas en: **{cluster_selected}**")

    fig2 = px.bar(
        cluster_df, x="Machine", y="Num_Failures",
        color="Num_Failures", color_continuous_scale="Blues",
        title="Fallos por Máquina"
    )
    st.plotly_chart(fig2, use_container_width=True)

# ===============================
# TAB 3 — EQ TYPE
# ===============================
with tab3:
    st.markdown("## 🤖 EQ Type que más falla")

    eq_fail = df_events.groupby("EQ Type")["Downtime"].count().reset_index()
    eq_fail = eq_fail.sort_values(by="Downtime", ascending=False)

    fig3 = px.bar(eq_fail, x="EQ Type", y="Downtime",
                  color="Downtime", color_continuous_scale="Tealgrn")
    st.plotly_chart(fig3, use_container_width=True)

# ===============================
# TAB 4 — RAW TABLE
# ===============================
with tab4:
    st.markdown("## 📊 Tabla del Clúster Seleccionado")
    st.dataframe(cluster_df)

# ===============================
# GAUGE — LEVEL OF RISK
# ===============================
pred_fail = float(m["Weekly_Pred_Scaled"])
max_risk = df_final["Weekly_Pred_Scaled"].max()

if max_risk == 0:
    max_risk = 1

gauge_value = (pred_fail / max_risk) * 100

# =====================================================
# 📅 PLAN DE MANTENIMIENTO RECOMENDADO
# =====================================================

st.markdown("## 🛠️ Plan de Mantenimiento Recomendado")

events_machine = df_events[df_events["Machine Name"] == machine_selected]

if not events_machine.empty:
    eq_type_machine = (
        events_machine.groupby("EQ Type")["Downtime"]
        .count()
        .reset_index()
        .sort_values(by="Downtime", ascending=False)
        .iloc[0]["EQ Type"]
    )
else:
    eq_type_machine = "No registrado"

maint_days = m["Maintenance_Recommended"]

pred_fail_real = float(m["Weekly_Prediction"])

reco = f"""
### 📌 Resumen de Mantenimiento para **{machine_selected}**

🔧 **Mantenimiento recomendado en:** {maint_days}

📉 **Predicción de fallas esta semana:** {pred_fail_real:.4f} fallas  
*(valor real antes de escalamiento)*  

⚙️ **Tipo de equipo más crítico:** {eq_type_machine}

🛠️ **Responsable sugerido:** Área especializada en **{eq_type_machine}**
"""

# Estado
if pred_fail_real >= 2:
    reco += "\n🚨 **ALERTA:** Alta probabilidad de falla."
elif pred_fail_real >= 1:
    reco += "\n⚠️ **Atención:** Probabilidad media."
else:
    reco += "\n✅ **Estable:** Baja probabilidad de falla esta semana."

st.markdown(reco)
