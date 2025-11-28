import streamlit as st
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import plotly.express as px
import plotly.graph_objs as go

# ===============================
# CONFIGURACIÓN
# ===============================
st.set_page_config(page_title="FLEX Predictivo", layout="wide")

st.markdown(
    "<h1 style='text-align:center; color:#4DA3FF;'>🛠️ Dashboard de Mantenimiento Predictivo FLEX</h1>",
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
# LIMPIAR / AJUSTAR DATOS
# ===============================
df_final["Weekly_Prediction"] = pd.to_numeric(df_final["Weekly_Prediction"], errors="coerce").fillna(0)
df_final["Maintenance_Recommended"] = df_final["Maintenance_Recommended"].astype(str)

# ===============================
# CÁLCULO AUTOMÁTICO DE PESOS
# ===============================
failures = df_final["Num_Failures"]
severity = df_final["Avg_Severity"]
downtime = df_final["Total_Downtime"]

cv_fail = failures.std() / failures.mean()
cv_sev  = severity.std() / severity.mean()
cv_down = downtime.std() / downtime.mean()

total_cv = cv_fail + cv_sev + cv_down

w_fail = cv_fail / total_cv
w_sev  = cv_sev  / total_cv
w_down = cv_down / total_cv

# ===============================
# NORMALIZAR VARIABLES
# ===============================
scaler = MinMaxScaler()

df_final["Norm_Failures"] = scaler.fit_transform(df_final[["Num_Failures"]])
df_final["Norm_Severity"] = scaler.fit_transform(df_final[["Avg_Severity"]])
df_final["Norm_Downtime"] = scaler.fit_transform(df_final[["Total_Downtime"]])

# ===============================
# RISK SCORE FINAL (0–100)
# ===============================
df_final["Risk_Score"] = (
    w_fail * df_final["Norm_Failures"] +
    w_sev  * df_final["Norm_Severity"] +
    w_down * df_final["Norm_Downtime"]
) * 100

# ===============================
# SIDEBAR
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

    filtered_machines = df_final[df_final["Cluster_Name"] == cluster_selected]["Machine"].unique()
    machine_selected = st.selectbox("Selecciona una máquina:", filtered_machines)

# ===============================
# GET MACHINE ROW
# ===============================
m = df_final[df_final["Machine"] == machine_selected].iloc[0]

# ===============================
# GAUGE DEL NIVEL DE RIESGO
# ===============================

st.markdown("## 🎯 Nivel de Riesgo (Gauge)")

risk_percent = float(m["Risk_Score"])

fig_gauge = go.Figure(go.Indicator(
    mode="gauge+number",
    value=risk_percent,
    title={'text': "Nivel de Riesgo (%)"},
    gauge={
        "axis": {"range": [0, 100]},
        "bar": {"color": "black"},
        "steps": [
            {"range": [0, 40], "color": "lightgreen"},
            {"range": [40, 70], "color": "yellow"},
            {"range": [70, 100], "color": "red"},
        ]
    }
))

st.plotly_chart(fig_gauge, use_container_width=True)

# ===============================
# PLAN DE MANTENIMIENTO (VISUAL)
# ===============================
st.markdown("## 🛠️ Plan de Mantenimiento Recomendado")

pred_fail_real = float(m["Weekly_Prediction"])
maint_days = m["Maintenance_Recommended"]
eq_type_machine = df_events[df_events["Machine Name"] == machine_selected]["EQ Type"].mode()[0] \
    if machine_selected in df_events["Machine Name"].values else "N/A"

# BLOQUES VISUALES
colA, colB = st.columns(2)

with colA:
    st.markdown(f"""
    <div style="background:#1E90FF; padding:18px; border-radius:10px; color:white;">
        <h3>🔧 Mantenimiento recomendado</h3>
        <p style="font-size:24px;"><b>{maint_days}</b></p>
    </div>
    """, unsafe_allow_html=True)

with colB:
    st.markdown(f"""
    <div style="background:#6C63FF; padding:18px; border-radius:10px; color:white;">
        <h3>⚙️ Tipo de equipo más crítico</h3>
        <p style="font-size:24px;"><b>{eq_type_machine}</b></p>
    </div>
    """, unsafe_allow_html=True)

colC, colD = st.columns(2)

with colC:
    st.markdown(f"""
    <div style="background:#FF8C00; padding:18px; border-radius:10px; color:white;">
        <h3>📉 Predicción de fallas esta semana</h3>
        <p style="font-size:23px;"><b>{pred_fail_real:.6f}</b></p>
    </div>
    """, unsafe_allow_html=True)

with colD:
    st.markdown(f"""
    <div style="background:#2ECC71; padding:18px; border-radius:10px; color:white;">
        <h3>🧑‍🔧 Responsable sugerido</h3>
        <p style="font-size:23px;"><b>Área especializada en {eq_type_machine}</b></p>
    </div>
    """, unsafe_allow_html=True)

# ESTADO FINAL
if risk_percent > 70:
    st.markdown("🚨 <b>Alerta crítica:</b> probabilidad alta de falla.", unsafe_allow_html=True)
elif risk_percent > 40:
    st.markdown("⚠️ <b>Atención:</b> riesgo medio.", unsafe_allow_html=True)
else:
    st.markdown("🟩 <b>Estable:</b> baja probabilidad de falla.", unsafe_allow_html=True)

# ===============================
# HISTÓRICO + PREDICCIÓN (MACHINE)
# ===============================
st.markdown("---")
st.markdown("### 📈 Tendencia Histórica y Predicción de Fallas (Máquina)")

machine_hist = df_events[df_events["Machine Name"] == machine_selected].copy()

if machine_hist.empty:
    st.warning("⚠️ No hay eventos de falla registrados para esta máquina.")
else:
    machine_hist["Date"] = pd.to_datetime(machine_hist["Date"])
    machine_hist["YearMonth"] = machine_hist["Date"].dt.to_period("M").astype(str)

    failures_by_month = machine_hist.groupby("YearMonth").size().reset_index(name="Failures")

    future_date = (machine_hist["Date"].max() + pd.DateOffset(weeks=1)).strftime("%Y-%m")

    fig_m = go.Figure()
    fig_m.add_trace(go.Scatter(x=failures_by_month["YearMonth"], y=failures_by_month["Failures"],
                               mode="lines+markers", line=dict(color="#4DA3FF")))
    fig_m.add_trace(go.Scatter(x=[future_date], y=[pred_fail_real], mode="markers+text",
                               text=["Forecast"], marker=dict(color="orange", size=12)))

    st.plotly_chart(fig_m, use_container_width=True)

# ===============================
# HISTÓRICO + PREDICCIÓN (CLÚSTER)
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

    failures_cluster = cluster_events.groupby("YearMonth").size().reset_index(name="Failures")
    cluster_forecast = cluster_df["Weekly_Prediction"].sum()
    future_cluster_date = (cluster_events["Date"].max() + pd.DateOffset(weeks=1)).strftime("%Y-%m")

    fig_c = go.Figure()
    fig_c.add_trace(go.Scatter(x=failures_cluster["YearMonth"], y=failures_cluster["Failures"],
                               mode="lines+markers", line=dict(color="#008080")))
    fig_c.add_trace(go.Scatter(x=[future_cluster_date], y=[cluster_forecast],
                               mode="markers+text", text=["Forecast"],
                               marker=dict(color="red", size=12)))

    st.plotly_chart(fig_c, use_container_width=True)

# ===============================
# TABLAS Y GRÁFICAS EXTRA
# ===============================
st.markdown("---")
tab1, tab2, tab3 = st.tabs(["📊 Tabla del Clúster", "🏭 Fallas por Máquina", "🤖 Fallas por EQ Type"])

with tab1:
    st.dataframe(cluster_df)

with tab2:
    fig2 = px.bar(cluster_df, x="Machine", y="Num_Failures",
                  color="Num_Failures", color_continuous_scale="Blues")
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    eq_fail = df_events.groupby("EQ Type")["Downtime"].count().reset_index()
    eq_fail = eq_fail.sort_values(by="Downtime", ascending=False)
    fig3 = px.bar(eq_fail, x="EQ Type", y="Downtime",
                  color="Downtime", color_continuous_scale="Tealgrn")
    st.plotly_chart(fig3, use_container_width=True)
