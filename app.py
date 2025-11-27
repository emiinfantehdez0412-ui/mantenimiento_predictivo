import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Dashboard de Mantenimiento Predictivo", layout="wide")

st.title("🔧 Dashboard de Mantenimiento Predictivo")
st.write("Visualización dinámica basada en clustering y predicciones TSB.")

# --------------------------
# LOAD FINAL TABLE
# --------------------------
@st.cache_data
def load_final_table():
    return pd.read_excel("final_table.xlsx")

final_table = load_final_table()

# --------------------------
# SIDEBAR FILTERS
# --------------------------
st.sidebar.header("Filtros")

clusters = sorted(final_table["Cluster"].unique())
cluster_sel = st.sidebar.selectbox("Selecciona un Cluster:", clusters)

machines = final_table[final_table["Cluster"] == cluster_sel]["Machine"].unique()
machine_sel = st.sidebar.selectbox("Selecciona una Máquina:", machines)

# --------------------------
# SHOW MACHINE INFO
# --------------------------
machine_data = final_table[final_table["Machine"] == machine_sel].iloc[0]

st.subheader(f"📌 Información de la máquina: **{machine_sel}**")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Cluster", int(machine_data["Cluster"]))
with col2:
    st.metric("Riesgo", machine_data["Cluster_Name"])
with col3:
    st.metric("Fallos semanales estimados", f"{machine_data['Weekly_Prediction']:.4f}")

st.divider()

# --------------------------
# MAINTENANCE RECOMMENDATION
# --------------------------
st.subheader("🛠️ Recomendación de mantenimiento preventivo")

st.info(
    f"**Dar mantenimiento cada:** {machine_data['Maintenance_Recommended']} días\n\n"
    f"(Basado en TBP promedio = {machine_data['Avg_TBF']:.2f})"
)

# --------------------------
# SHOW FORECAST ARRAY
# --------------------------
st.subheader("📈 Predicción semanal (TSB)")

pred = machine_data["Best_Prediction"]

if isinstance(pred, str):
    try:
        pred = eval(pred)  # convert string list to real list
    except:
        pred = [0]

fig, ax = plt.subplots()
ax.plot(pred, marker="o", color="orange")
ax.set_title(f"Pronóstico TSB – {machine_sel}")
ax.set_xlabel("Semanas futuras")
ax.set_ylabel("Fallos esperados")
st.pyplot(fig)
