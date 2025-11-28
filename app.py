import streamlit as st
import pandas as pd
import numpy as np
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
# CÁLCULO DE PESOS
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
# NORMALIZACIÓN MANUAL
# ===============================
def normalize(series):
    return (series - series.min()) / (series.max() - series.min() + 1e-12)

df_final["Norm_Failures"] = normalize(df_final["Num_Failures"])
df_final["Norm_Severity"] = normalize(df_final["Avg_Severity"])
df_final["Norm_Downtime"] = normalize(df_final["Total_Downtime"])

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
# GAUGE
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
# PLAN DE MANTENIMIENTO
# ===============================
st.markdown("## 🛠️ Plan de Mantenimiento Recomendado")

pred_fail_real = float(m["Weekly_Prediction"])
maint_days = m["Maintenance_Recommended"]

eq_type_machine = df_events[df_events["Machine Name"] == machine_selected]["EQ Type"].mode()[0] \
    if machine_selected in df_events["Machine Name"].values else "N/A"

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

if risk_percent > 70:
    st.markdown("🚨 <b>Alerta crítica:</b> probabilidad alta de falla.", unsafe_allow_html=True)
elif risk_percent > 40:
    st.markdown("⚠️ <b>Atención:</b> riesgo medio.", unsafe_allow_html=True)
else:
    st.markdown("🟩 <b>Estable:</b> baja probabilidad de falla.", unsafe_allow_html=True)
