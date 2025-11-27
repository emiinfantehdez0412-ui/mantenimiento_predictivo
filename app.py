import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# --------------------
# CONFIG
# --------------------
st.set_page_config(page_title="Dashboard Predictivo de Mantenimiento", layout="wide")

st.title("📊 Dashboard de Mantenimiento Predictivo")
st.write("Predicciones basadas en clustering + modelo TSB para fallas semanales.")


# --------------------
# SUBIR ARCHIVO
# --------------------
st.header("📁 Tabla final de predicciones y calendario de mantenimiento")

uploaded = st.file_uploader("Sube la tabla_final.xlsx:", type=["xlsx"])

if uploaded is None:
    st.info("Sube el archivo **tabla_final.xlsx** para continuar.")
    st.stop()

df = pd.read_excel(uploaded)
st.success("Archivo cargado correctamente ✔️")

st.subheader("Vista general de los datos")
st.dataframe(df, use_container_width=True)


# --------------------
# SELECCIÓN DE MÁQUINA
# --------------------
if "Machine Name" not in df.columns:
    st.error("❌ La base no contiene la columna 'Machine Name'. Revisa el archivo.")
    st.stop()

machine = st.selectbox("Selecciona una máquina:", df["Machine Name"].unique())


machine_df = df[df["Machine Name"] == machine]


# --------------------
# HISTÓRICO DE FALLAS
# --------------------
st.subheader(f"📉 Historial de fallas - {machine}")

failure_cols = ["Downtime", "Tiempo Paro", "Total Stop Time(Hours)"]

found_cols = [c for c in failure_cols if c in machine_df.columns]

if len(found_cols) == 0:
    st.warning("⚠ No se encontraron columnas de fallas ('Downtime', 'Tiempo Paro', etc.)")
else:
    col = found_cols[0]
    st.write(f"Usando la columna de fallas: **{col}**")

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(machine_df[col].values, color="orange")
    ax.set_title(f"Fallos históricos – {machine}")
    ax.set_xlabel("Registro")
    ax.set_ylabel("Fallas")
    st.pyplot(fig)


# --------------------
# MODELO TSB PARA PREDICCIÓN
# --------------------
def tsb(series, alpha=0.3, beta=0.1, h=7):
    y = np.array(series, dtype=float)
    demand = (y > 0).astype(int)
    non_zero = y.copy().astype(float)
    non_zero[y == 0] = np.nan

    p = demand[0]
    z = np.nanmean(non_zero)

    P = [p]
    Z = [z]

    for t in range(1, len(y)):
        if demand[t] == 0:
            Z.append(Z[-1])
        else:
            Z.append((1-beta)*Z[-1] + beta*(non_zero[t] - Z[-1]))

        P.append((1-alpha)*P[-1] + alpha*(demand[t] - P[-1]))

    forecast = np.array(P[-1] * Z[-1] * np.ones(h))
    return forecast


# --------------------
# GENERAR PREDICCIÓN
# --------------------
st.subheader("🔮 Predicción semanal de fallas (TSB)")

series = machine_df[col].values

if len(series) < 10:
    st.warning("⚠ No hay suficientes datos para predecir.")
    st.stop()

pred = tsb(series, h=7)

st.write("**Predicción para las siguientes 7 semanas:**")
st.write(pred)

fig2, ax2 = plt.subplots(figsize=(12, 4))
ax2.plot(series, label="Histórico")
ax2.plot(range(len(series), len(series)+7), pred, label="Pronóstico TSB", color="red")
ax2.set_title(f"Predicción de fallas – {machine}")
ax2.legend()
st.pyplot(fig2)


# --------------------
# CALENDARIO DE MANTENIMIENTO
# --------------------
st.subheader("🛠️ Sugerencia de mantenimiento preventivo")

umbral = st.slider(
    "Selecciona el umbral de fallas para recomendar mantenimiento:",
    0.5, 10.0, 2.0, 0.5
)

weeks_trigger = np.where(pred >= umbral)[0]

if len(weeks_trigger) == 0:
    st.success("👏 No se recomienda mantenimiento en las próximas 7 semanas.")
else:
    st.error(f"⚠ Se recomienda mantenimiento en **{weeks_trigger[0] + 1} semanas**.")
    st.write("Porque la predicción supera el umbral seleccionado.")


st.success("Dashboard generado correctamente ✔️")
