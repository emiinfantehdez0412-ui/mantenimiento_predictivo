import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Dashboard de Mantenimiento Predictivo", layout="wide")

# ==============================
#  1. Cargar datos
# ==============================
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("final_table.xlsx")
        return df
    except:
        st.error("❌ No se encontró el archivo final_table.xlsx en el repositorio.")
        st.stop()

df = load_data()

# ==============================
# Título
# ==============================
st.title("📊 Dashboard de Mantenimiento Predictivo")
st.write("Predicciones semanales, clústers de riesgo y calendario de mantenimiento recomendado.")

# ==============================
# 2. Barra lateral: filtros
# ==============================
st.sidebar.header("🔍 Filtros")

clusters = sorted(df["Cluster"].unique())
selected_cluster = st.sidebar.selectbox("Selecciona un clúster:", clusters)

machines_cluster = df[df["Cluster"] == selected_cluster]["Machine"].unique()
selected_machine = st.sidebar.selectbox("Selecciona una máquina:", machines_cluster)

machine_df = df[df["Machine"] == selected_machine].iloc[0]

# ==============================
# 3. Tarjetas de resumen
# ==============================
st.subheader(f"📌 Resumen — {selected_machine}")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Cluster", machine_df["Cluster"])
col2.metric("Clasificación", machine_df["Cluster_Name"])
col3.metric("Predicción semanal esperada", f"{machine_df['Weekly_Prediction']:.5f}")
col4.metric("TBF promedio (semanas)", f"{machine_df['Avg_TBF']:.2f}")

# Recomendación
st.success(
    f"🛠 **Mantenimiento recomendado en aproximadamente:** {machine_df['Maintenance_Recommended']}"
)

# ==============================
# 4. Gráfica de tendencia semanal (Train/Test/Forecast)
# ==============================
st.subheader("📈 Tendencia semanal histórica y predicción (TSB)")

try:
    if "Weekly_Prediction" in machine_df:
        forecast_val = machine_df["Weekly_Prediction"]

        forecast_vals = np.array([forecast_val] * 7)

        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(forecast_vals, label="Predicción TSB", color="red")
        ax.set_title(f"Predicción semanal - {selected_machine}")
        ax.set_ylabel("Fallas por semana")
        ax.set_xlabel("Semana futura (1-7)")
        ax.grid(True)
        ax.legend()
        st.pyplot(fig)
    else:
        st.warning("⚠ Esta máquina no tiene columna 'Weekly_Prediction'.")
except Exception as e:
    st.warning("⚠ No se pudo graficar la predicción TSB.")
    st.write(e)

# ==============================
# 5. Mostrar tabla completa
# ==============================
st.subheader("📄 Tabla completa de predicciones")
st.dataframe(df)
