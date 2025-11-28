import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from statsmodels.tsa.holtwinters import ExponentialSmoothing

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

# ================================================
# 📌 FUNCIÓN DE PRONÓSTICO DE FALLAS (HOLT-WINTERS)
# ================================================
def forecast_failures_machine(df_events, machine_name):

    df_m = df_events[df_events["Machine Name"] == machine_name].copy()

    if df_m.empty:
        return 0

    df_m["Date"] = pd.to_datetime(df_m["Date"])
    df_m["YearMonth"] = df_m["Date"].dt.to_period("M").astype(str)

    monthly = (
        df_m.groupby("YearMonth")
        .size()
        .reset_index(name="Failures")
    )
    monthly["YearMonth"] = pd.to_datetime(monthly["YearMonth"])

    if len(monthly) < 3:
        return monthly["Failures"].mean() / 4.345

    try:
        model = ExponentialSmoothing(
            monthly["Failures"],
            trend="add",
            seasonal=None
        ).fit()

        pred_month = model.forecast(1).iloc[0]
        pred_week = pred_month / 4.345
        return pred_week

    except:
        return monthly["Failures"].mean() / 4.345


# ===============================
# SIDEBAR FILTERS – CASCADA + BADGE
# ===============================
with st.sidebar:
    st.header("🔍 Filtros")

    clusters = df_final["Cluster_Name"].unique()
    cluster_selected = st.selectbox("Selecciona un clúster:", clusters)

    if "HIGH" in cluster_selected.upper():
        risk_color = "#E74C3C"
        risk_text  = "🔴 HIGH RISK"
    else:
        risk_color = "#2ECC71"
        risk_text  = "🟢 LOW RISK"

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

    filtered_machines = df_final[df_final["Cluster_Name"] == cluster_selected]["Machine"].unique()
    machine_selected = st.selectbox("Selecciona una máquina:", filtered_machines)


# ===============================
# CARD FUNCTION
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

# ==========================================================================================
# TAB 1 — MÁQUINA
# ==========================================================================================
with tab1:

    st.markdown("## 📌 Información de la Máquina")
    m = df_final[df_final["Machine"] == machine_selected].iloc[0]

    col1, col2, col3, col4 = st.columns(4)
    with col1: metric_card("Failure Rate", round(m["Failure_Rate"], 4))
    with col2: metric_card("Avg Severity", round(m["Avg_Severity"], 4))
    with col3: metric_card("Total Downtime", round(m["Total_Downtime"], 2))
    with col4: metric_card("Número de Fallas", int(m["Num_Failures"]))

    st.markdown("---")

    # =======================
    # HISTÓRICO + PREDICCIÓN
    # =======================
    st.markdown("### 📈 Tendencia Histórica y Predicción de Fallas (Máquina)")

    machine_hist = df_events[df_events["Machine Name"] == machine_selected].copy()

    if machine_hist.empty:
        st.warning("⚠️ No hay eventos de falla registrados para esta máquina.")
    else:
        machine_hist["Date"] = pd.to_datetime(machine_hist["Date"])
        machine_hist["YearMonth"] = machine_hist["Date"].dt.to_period("M").astype(str)

        failures_by_month = (
            machine_hist.groupby("YearMonth")
            .size()
            .reset_index(name="Failures")
        )

        # Nueva predicción
        forecast_value = forecast_failures_machine(df_events, machine_selected)
        future_date = (machine_hist["Date"].max() + pd.DateOffset(weeks=1)).strftime("%Y-%m")

        fig_m = go.Figure()
        fig_m.add_trace(go.Scatter(
            x=failures_by_month["YearMonth"],
            y=failures_by_month["Failures"],
            mode="lines+markers",
            name="Fallas históricas",
            line=dict(color="#4DA3FF", width=3)
        ))

        fig_m.add_trace(go.Scatter(
            x=[future_date],
            y=[forecast_value],
            mode="markers+text",
            text=["Forecast"],
            textposition="top center",
            marker=dict(color="orange", size=12),
            name="Predicción"
        ))

        fig_m.update_layout(
            title=f"Fallas Históricas + Predicción – {machine_selected}",
            xaxis_title="Mes",
            yaxis_title="Número de fallas",
            template="plotly_white"
        )
        st.plotly_chart(fig_m, use_container_width=True)

    st.markdown("## 🛠️ Plan de Mantenimiento Recomendado")

    pred_fail = forecast_failures_machine(df_events, machine_selected)
    maint_days = m["Maintenance_Recommended"]

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

# =====================================================
# 📅 PLAN DE MANTENIMIENTO RECOMENDADO — CARD STYLE
# =====================================================

st.markdown("## 🛠️ Plan de Mantenimiento Recomendado")
st.markdown(f"### 📌 Resumen de Mantenimiento para **{machine_selected}**")
st.markdown("")

# ---------- Tarjetas visuales ----------
def maintenance_card(title, value, icon="🔧", color="#1F618D"):
    st.markdown(
        f"""
        <div style="
            background-color:{color};
            padding:18px;
            border-radius:12px;
            color:white;
            text-align:center;
            font-size:18px;
            box-shadow: 0 0 10px rgba(0,0,0,0.3);
        ">
            <div style="font-size:32px;">{icon}</div>
            <b>{title}</b><br>
            <span style="font-size:26px;">{value}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

colA, colB, colC, colD = st.columns(4)

with colA:
    maintenance_card("Mant. recomendado", f"{maint_days} días", "🔧", "#2471A3")

with colB:
    maintenance_card("Predicción semanal", f"{pred_fail:.2f} fallas", "📉", "#2E86C1")

with colC:
    maintenance_card("EQ crítico", eq_type_machine, "⚙️", "#117864")

with colD:
    maintenance_card("Responsable", f"{eq_type_machine}", "🛠️", "#5D6D7E")

# ---------- Semáforo de riesgo ----------
st.markdown("---")

if pred_fail >= 2:
    st.markdown("🚨 **ALERTA:** Alta probabilidad de falla. Priorizar mantenimiento urgente.")
elif pred_fail >= 1:
    st.markdown("⚠️ **Atención:** Probabilidad media de falla esta semana.")
else:
    st.markdown("🟢 **Estable:** Baja probabilidad de falla esta semana.")


# ==========================================================================================
# TAB 2 — CLUSTER
# ==========================================================================================
with tab2:

    st.markdown(f"## 🏭 Máquinas en: **{cluster_selected}**")
    cluster_df = df_final[df_final["Cluster_Name"] == cluster_selected]

    fig_cl = px.bar(
        cluster_df, x="Machine", y="Num_Failures", color="Num_Failures",
        title="Fallos por Máquina", color_continuous_scale="Blues"
    )
    fig_cl.update_layout(template="plotly_white")
    st.plotly_chart(fig_cl, use_container_width=True)


# ==========================================================================================
# TAB 3 — EQ TYPE
# ==========================================================================================
with tab3:

    st.markdown("## 🤖 EQ Type que más falla")
    eq_fail = df_events.groupby("EQ Type")["Downtime"].count().reset_index()
    eq_fail = eq_fail.sort_values(by="Downtime", ascending=False)

    fig3 = px.bar(
        eq_fail, x="EQ Type", y="Downtime", color="Downtime",
        color_continuous_scale="Tealgrn"
    )
    fig3.update_layout(template="plotly_white")
    st.plotly_chart(fig3, use_container_width=True)

    top_eq = eq_fail.iloc[0]
    metric_card(f"EQ Type Más Crítico", f"{top_eq['EQ Type']} ({top_eq['Downtime']} fallas)", "#117864")


# ==========================================================================================
# TAB 4 — RAW TABLE
# ==========================================================================================
with tab4:
    st.markdown("## 📊 Tabla del Clúster Seleccionado")
    st.dataframe(cluster_df)
