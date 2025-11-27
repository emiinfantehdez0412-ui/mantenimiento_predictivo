import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Dashboard de Mantenimiento Predictivo", layout="wide")

st.title("📊 Dashboard de Mantenimiento Predictivo")
st.write("Predicciones basadas en clustering + TSB para fallas semanales.")

# --- Cargar la tabla final ---
st.header("📁 Tabla final de predicciones y calendario de mantenimiento")

uploaded_file = st.file_uploader("Sube la tabla_final.xlsx", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.dataframe(df)

    # Seleccionar máquina
    machine = st.selectbox("Selecciona una máquina:", df["Machine"].unique())

    mdf = df[df["Machine"] == machine].iloc[0]

    st.subheader(f"🔧 Recomendación para: **{machine}**")

    st.write(f"**Cluster:** {mdf['Cluster']}")
    st.write(f"**Modelo óptimo:** {mdf['Best_Model']}")
    st.write(f"**Siguiente mantenimiento recomendado:** `{mdf['Maintenance_Week']}`")

    st.write("### Predicción semanal:")
    st.line_chart(eval(mdf["Best_Prediction"]))
else:
    st.info("Sube el archivo `tabla_final.xlsx` para continuar.")
