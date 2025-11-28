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
    st.markdown("### 📈 Tendencia Histórica")

    machine_hist = df_events[df_events["Machine Name"] == machine_selected]

    if machine_hist.empty:
        st.warning("No hay datos históricos.")
    else:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=machine_hist["Date"],
            y=machine_hist["Downtime"],
            mode="lines+markers",
            line=dict(color="#4DA3FF", width=3),
            marker=dict(size=6)
        ))
        fig.update_layout(
            title=f"Downtime – {machine_selected}",
            xaxis_title="Fecha",
            yaxis_title="Downtime",
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("### 🔮 Predicción y Mantenimiento")

    col1, col2 = st.columns(2)
    with col1:
        metric_card("Predicción Semanal", round(m["Weekly_Prediction"], 3), "#1E8449")
    with col2:
        metric_card("Mantenimiento Recomendado", m["Maintenance_Recommended"], "#27AE60")

    st.markdown("---")
    st.markdown("### 📊 Métricas del Modelo")

    col1, col2, col3 = st.columns(3)
    with col1:
        metric_card("Modelo", m["Best_Model"], "#6C3483")
    with col2:
        metric_card("Best MAE", round(m["Best_MAE"], 5), "#76448A")
    with col3:
        metric_card("Predicción Final", round(m["Best_Prediction"], 5), "#BB8FCE")


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
