import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Dashboard Predictivo", layout="wide")

st.title("🔧 Dashboard de Mantenimiento Predictivo")
st.write("Este dashboard combina la base original de mantenimiento con la tabla procesada del modelo predictivo.")

# ===============================
# 1. CARGA DE ARCHIVOS
# ===============================

st.sidebar.header("📂 Carga de archivos")

orig_file = st.sidebar.file_uploader("📄 Sube la base ORIGINAL (Mantenimiento FLEX.xlsx)", type=["xlsx"])
proc_file = st.sidebar.file_uploader("📊 Sube la tabla PROCESADA (final_table.xlsx)", type=["xlsx"])

if orig_file:
    df_orig = pd.read_excel(orig_file)
    st.sidebar.success("Base original cargada correctamente.")

if proc_file:
    df_proc = pd.read_excel(proc_file)
    st.sidebar.success("Tabla procesada cargada correctamente.")

# Solo continuar si ambas tablas están cargadas
if not (orig_file and proc_file):
    st.warning("⚠️ Sube ambos archivos para activar el dashboard.")
    st.stop()

# ===============================
# 2. PREPARACIÓN DE DATOS
# ===============================

df_orig["Date"] = pd.to_datetime(df_orig["Date"], errors="coerce")

# ===============================
# 3. FILTROS DINÁMICOS
# ===============================

st.sidebar.header("🔍 Filtros")

clusters = sorted(df_proc["Cluster"].unique())
selected_cluster = st.sidebar.selectbox("Selecciona un clúster:", clusters)

machines = sorted(df_proc[df_proc["Cluster"] == selected_cluster]["Machine"].unique())
selected_machine = st.sidebar.selectbox("Selecciona una máquina:", machines)

# Filtros desde la base original
shifts = sorted(df_orig["Shift"].dropna().unique())
selected_shift = st.sidebar.multiselect("Selecciona Turnos (Shift):", shifts, default=shifts)

eq_types = sorted(df_orig["EQ Type"].dropna().unique())
selected_eq = st.sidebar.multiselect("Selecciona EQ Type:", eq_types, default=eq_types)

# ===============================
# 4. KPIS DE LA MÁQUINA
# ===============================

machine_row = df_proc[df_proc["Machine"] == selected_machine].iloc[0]

col1, col2 = st.columns(2)

with col1:
    st.success(f"🛠️ Mantenimiento recomendado: **{machine_row['Maintenance_Recommended']}** días")

with col2:
    st.info(f"📌 Categoría: **{machine_row['Cluster_Name']}**")


# ===============================
# 5. GRÁFICA HISTÓRICA POR MÁQUINA
# ===============================

st.subheader("📈 Tendencia semanal histórica de fallas")

machine_data = df_orig[
    (df_orig["Machine Name"] == selected_machine) &
    (df_orig["Shift"].isin(selected_shift)) &
    (df_orig["EQ Type"].isin(selected_eq))
]

if machine_data.empty:
    st.warning("⚠️ No hay datos históricos con los filtros seleccionados.")
else:
    weekly = machine_data.resample("W", on="Date").size()

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(weekly.index, weekly.values, marker="o", color="blue")
    ax.set_title(f"Histórico de fallas por semana - {selected_machine}")
    ax.set_ylabel("Fallas")
    ax.grid(True)
    st.pyplot(fig)

# ===============================
# 6. GRÁFICA DEL CLÚSTER COMPLETO
# ===============================

st.subheader(f"📊 Tendencia semanal del clúster {selected_cluster}")

cluster_machines = df_proc[df_proc["Cluster"] == selected_cluster]["Machine"]
cluster_data = df_orig[df_orig["Machine Name"].isin(cluster_machines)]

if cluster_data.empty:
    st.warning("⚠️ No hay datos históricos para este clúster.")
else:
    weekly_cluster = cluster_data.resample("W", on="Date").size()

    fig2, ax2 = plt.subplots(figsize=(10, 4))
    ax2.plot(weekly_cluster.index, weekly_cluster.values, color="green")
    ax2.set_title(f"Histórico semanal – Clúster {selected_cluster}")
    ax2.set_ylabel("Fallas")
    ax2.grid(True)
    st.pyplot(fig2)

# ===============================
# 7. GRÁFICA DE PREDICCIÓN TSB
# ===============================

st.subheader("🔮 Predicción semanal TSB")

if "Weekly_Prediction" not in df_proc.columns:
    st.warning("⚠️ La tabla procesada no contiene la columna Weekly_Prediction.")
else:
    pred_val = machine_row["Weekly_Prediction"]

    fig3, ax3 = plt.subplots(figsize=(10, 4))
    ax3.plot(range(1, 8), [pred_val] * 7, color="red", marker="o")
    ax3.set_title(f"Predicción semanal TSB - {selected_machine}")
    ax3.set_xlabel("Semana futura")
    ax3.set_ylabel("Fallas esperadas")
    ax3.grid(True)
    st.pyplot(fig3)

# ===============================
# 8. TABLA COMPLETA DE PREDICCIONES
# ===============================

st.subheader("📋 Tabla completa de predicciones (del archivo procesado)")

st.dataframe(df_proc.style.highlight_max(axis=0))
