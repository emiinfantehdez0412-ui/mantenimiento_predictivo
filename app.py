import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Dashboard de Mantenimiento Predictivo", layout="wide")

# ---------------------------
# TÍTULO PRINCIPAL
# ---------------------------
st.title("🔧 Dashboard de Mantenimiento Predictivo")
st.markdown("Predicciones basadas en clustering + TSB para fallas semanales.")

# ---------------------------
# CARGA DE ARCHIVOS
# ---------------------------
st.sidebar.header("📂 Carga de archivos")

# Archivo original (Mantenimiento FLEX)
original_file = st.sidebar.file_uploader("Sube la base ORIGINAL (Mantenimiento FLEX.xlsx)", type=["xlsx"])

# Archivo procesado desde Colab
processed_file = st.sidebar.file_uploader("Sube la tabla PROCESADA (final_table.xlsx)", type=["xlsx"])

# Si no están cargados ambos, detenemos
if not original_file:
    st.warning("📄 Sube la base ORIGINAL para continuar.")
    st.stop()

if not processed_file:
    st.warning("📄 Sube la tabla PROCESADA para continuar.")
    st.stop()

# Cargar archivos
df_original = pd.read_excel(original_file)
df_processed = pd.read_excel(processed_file)

required_cols = ["Machine", "Cluster", "Cluster_Name", "Weekly_Prediction",
                 "Avg_TBF", "Maintenance_Recommended", "MAE_Croston", "MAE_TSB",
                 "Best_Model", "Best_MAE"]

missing_cols = [c for c in required_cols if c not in df_processed.columns]

if missing_cols:
    st.error(f"❌ La tabla procesada NO contiene las columnas requeridas: {missing_cols}")
    st.stop()

st.success("✔ Archivos cargados correctamente.")

# ---------------------------
# FILTROS
# ---------------------------
clusters = sorted(df_processed["Cluster"].unique())
cluster_selected = st.sidebar.selectbox("Selecciona un clúster:", clusters)

machines_cluster = df_processed[df_processed["Cluster"] == cluster_selected]["Machine"].unique()
machine_selected = st.sidebar.selectbox("Selecciona una máquina:", machines_cluster)

# ---------------------------
# SELECCIÓN DE FILA DE LA MÁQUINA
# ---------------------------
machine_row = df_processed[df_processed["Machine"] == machine_selected].iloc[0]

# ---------------------------
# SECCIÓN 1: Mantenimiento Recomendado
# ---------------------------
st.header("🛠️ Mantenimiento recomendado")

maintenance_days = machine_row["Maintenance_Recommended"]

# Validación robusta
if pd.notnull(maintenance_days) and isinstance(maintenance_days, (int, float)):
    st.success(f"🔧 Se recomienda mantenimiento en aproximadamente **{maintenance_days:.1f} días**.")
else:
    st.warning("⚠ No hay suficiente información para calcular el mantenimiento recomendado.")

# ---------------------------
# SECCIÓN 2: Tendencia semanal histórica + predicción TSB
# ---------------------------
st.header("📉 Tendencia semanal histórica y predicción (TSB)")

if "Best_Prediction" in df_processed.columns:
    # Best_Prediction es LISTA → convertir
    pred_list = machine_row["Best_Prediction"]

    if isinstance(pred_list, str):
        try:
            pred_list = eval(pred_list)
        except:
            pred_list = None

    if isinstance(pred_list, list) and len(pred_list) > 0:
        plt.figure(figsize=(10,4))
        plt.plot(pred_list, marker="o", label="Predicción semanal (TSB)")
        plt.xlabel("Semana futura")
        plt.ylabel("Fallas esperadas")
        plt.legend()
        st.pyplot(plt)
    else:
        st.warning("⚠ No se pudo graficar la predicción TSB.")
else:
    st.warning("⚠ La columna 'Best_Prediction' no se encuentra en la tabla procesada.")

# ---------------------------
# SECCIÓN 3: Métricas de error (MAE)
# ---------------------------
st.header("📏 Métricas de error del modelo (MAE)")

mae_croston = machine_row["MAE_Croston"]
mae_tsb = machine_row["MAE_TSB"]
best_model = machine_row["Best_Model"]
best_mae = machine_row["Best_MAE"]

col1, col2, col3, col4 = st.columns(4)

def format_mae(val):
    if pd.notnull(val) and isinstance(val, (float, int)):
        return f"{val:.6f}"
    return "N/A"

col1.metric("MAE Croston", format_mae(mae_croston))
col2.metric("MAE TSB", format_mae(mae_tsb))
col3.metric("Mejor Modelo", str(best_model))
col4.metric("MAE del Mejor Modelo", format_mae(best_mae))

# ---------------------------
# SECCIÓN 4: Tabla completa
# ---------------------------
st.header("📋 Tabla completa de predicciones")
st.dataframe(df_processed)

# ---------------------------
# SECCIÓN 5: Información complementaria del archivo original
# ---------------------------
st.header("🗂 Datos originales de la máquina seleccionada")

machine_original = df_original[df_original["Machine Name"] == machine_selected]

if machine_original.empty:
    st.info("ℹ No se encontraron registros en el archivo original para esta máquina.")
else:
    st.dataframe(machine_original)
