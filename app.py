import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Dashboard de Mantenimiento Predictivo",
    layout="wide"
)

# ============================================================
#                       TÍTULO PRINCIPAL
# ============================================================
st.title("🔧 Dashboard de Mantenimiento Predictivo")
st.write("Predicciones basadas en clustering + TSB para fallas semanales.")

# ============================================================
#                   CARGA DE ARCHIVOS
# ============================================================
st.sidebar.header("📂 Carga de archivos")

original_file = st.sidebar.file_uploader(
    "Sube la base ORIGINAL (Mantenimiento FLEX.xlsx)",
    type=["xlsx"],
    key="original"
)

processed_file = st.sidebar.file_uploader(
    "Sube la tabla PROCESADA (final_table.xlsx)",
    type=["xlsx"],
    key="processed"
)

if original_file:
    st.sidebar.success("Base original cargada correctamente. ✅")

if processed_file:
    st.sidebar.success("Tabla procesada cargada correctamente. ✅")

# No continuar hasta cargar ambos archivos
if not original_file or not processed_file:
    st.warning("Por favor sube ambos archivos para continuar.")
    st.stop()

# ============================================================
#         CARGA DE DATAFRAMES DESDE LOS ARCHIVOS
# ============================================================
df_original = pd.read_excel(original_file)
df_processed = pd.read_excel(processed_file)

# Nombres obligatorios que DEBEN existir en el archivo procesado
expected_processed_cols = [
    "Machine", "Cluster", "Cluster_Name", "Weekly_Prediction",
    "Avg_TBF", "Maintenance_Recommended",
    "MAE_Croston", "MAE_TSB", "Best_Model", "Best_MAE"
]

missing_cols = [c for c in expected_processed_cols if c not in df_processed.columns]

if missing_cols:
    st.error(f"❌ La tabla procesada NO contiene todas las columnas requeridas:\n{missing_cols}")
    st.stop()

# ============================================================
#                   FILTROS LATERALES
# ============================================================
st.sidebar.header("🎛 Filtros")

cluster_list = sorted(df_processed["Cluster"].unique())
cluster_select = st.sidebar.selectbox("Selecciona un clúster:", cluster_list)

machines_in_cluster = df_processed[df_processed["Cluster"] == cluster_select]["Machine"]
machine_select = st.sidebar.selectbox("Selecciona una máquina:", machines_in_cluster)

# Extra: filtros desde la base original
shift_list = sorted(df_original["Shift"].dropna().unique())
shift_select = st.sidebar.multiselect("Filtro por Shift (opcional):", shift_list)

eq_list = sorted(df_original["EQ Type"].dropna().unique())
eq_select = st.sidebar.multiselect("Filtro por EQ Type (opcional):", eq_list)

# ============================================================
#            SELECCIÓN DE LA MÁQUINA EN LA TABLA PROCESADA
# ============================================================
machine_row = df_processed[df_processed["Machine"] == machine_select].iloc[0]

# ============================================================
#        SECCIÓN 1: MANTENIMIENTO RECOMENDADO
# ============================================================
st.subheader("🛠 Mantenimiento recomendado")

maintenance_days = machine_row["Maintenance_Recommended"]
st.success(f"🔧 Se recomienda mantenimiento en aproximadamente **{maintenance_days:.1f} días**.")

# ============================================================
#      SECCIÓN 2: TENDENCIA HISTÓRICA DE LA MÁQUINA (ORIGINAL)
# ============================================================
st.subheader("📈 Tendencia histórica por máquina (dataset original)")

df_machine_hist = df_original[df_original["Machine Name"] == machine_select]

if shift_select:
    df_machine_hist = df_machine_hist[df_machine_hist["Shift"].isin(shift_select)]

if eq_select:
    df_machine_hist = df_machine_hist[df_machine_hist["EQ Type"].isin(eq_select)]

if df_machine_hist.empty:
    st.warning("⚠ No hay datos históricos con los filtros seleccionados.")
else:
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df_machine_hist["Date"], df_machine_hist["Downtime"], color="blue")
    ax.set_title(f"Histórico de fallas – {machine_select}")
    ax.set_xlabel("Fecha")
    ax.set_ylabel("Downtime")
    st.pyplot(fig)

# ============================================================
#       SECCIÓN 3: PREDICCIÓN FUTURA POR CLÚSTER
# ============================================================
st.subheader("🔮 Predicción semanal futura por clúster")

cluster_rows = df_processed[df_processed["Cluster"] == cluster_select]

future_vals = cluster_rows["Weekly_Prediction"].head(7).values

fig2, ax2 = plt.subplots(figsize=(10, 4))
ax2.plot(range(1, len(future_vals)+1), future_vals, marker="o", color="orange")
ax2.set_title(f"Predicción TSB – Clúster {cluster_select}")
ax2.set_xlabel("Semana futura")
ax2.set_ylabel("Pred. de fallas")
st.pyplot(fig2)

# ============================================================
#       SECCIÓN 4: MÉTRICAS DE ERROR DEL MODELO
# ============================================================
st.subheader("📉 Métricas de error del modelo (MAE)")

mae_croston = machine_row["MAE_Croston"]
mae_tsb = machine_row["MAE_TSB"]
best_model = machine_row["Best_Model"]
best_mae = machine_row["Best_MAE"]

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("MAE Croston", f"{mae_croston:.4f}")

with col2:
    st.metric("MAE TSB", f"{mae_tsb:.4f}")

with col3:
    st.metric(f"Mejor modelo ({best_model})", f"{best_mae:.4f}")

# ============================================================
#       SECCIÓN 5: TABLA COMPLETA DE PREDICCIONES
# ============================================================
st.subheader("📄 Tabla completa de predicciones")

st.dataframe(df_processed)
