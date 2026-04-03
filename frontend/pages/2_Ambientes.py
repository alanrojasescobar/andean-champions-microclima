import pandas as pd
import streamlit as st

from api.client import get_ambiente, get_ambientes, get_estado_ambiente, get_historial_ambiente
from components.charts import plot_variable
from components.header import render_header

st.set_page_config(page_title="Ambientes", layout="wide")
render_header("Supervisión por Ambiente")

try:
    ambientes = get_ambientes()

    if not ambientes:
        st.warning("No existen ambientes registrados.")
        st.stop()

    opciones = {f"{a['nombre']} ({a['ambiente_id']})": a["ambiente_id"] for a in ambientes}
    seleccionado = st.selectbox("Selecciona un ambiente", list(opciones.keys()))
    ambiente_id = opciones[seleccionado]

    info = get_ambiente(ambiente_id)

    st.subheader("Información del ambiente")
    col1, col2, col3 = st.columns(3)
    col1.metric("Ambiente ID", info["ambiente_id"])
    col2.metric("Nombre", info["nombre"])
    col3.metric("Tipo", info.get("tipo") or "No definido")

    tabs = st.tabs(["Resumen", "Historial", "Actuadores"])

    with tabs[0]:
        try:
            estado = get_estado_ambiente(ambiente_id)
            sensores = estado.get("sensores", [])
            actuadores = estado.get("actuadores", {})

            if sensores:
                sensor = sensores[0]
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Temperatura", f"{sensor['temperatura']} °C" if sensor["temperatura"] is not None else "N/D")
                c2.metric("Humedad", f"{sensor['humedad']} %" if sensor["humedad"] is not None else "N/D")
                c3.metric("CO₂", f"{sensor['co2']} ppm" if sensor["co2"] is not None else "N/D")
                c4.metric("Estado sensor", sensor.get("estado_sensor") or "DESCONOCIDO")

                if len(sensores) > 1:
                    st.caption(f"Sensores reportando: {len(sensores)}. Se muestra el primero para el resumen.")
            else:
                st.info("Este ambiente aún no tiene sensores reportando.")

            st.markdown("### Estado de actuadores")
            a1, a2, a3 = st.columns(3)
            a1.metric("Calefactor", "Encendido" if actuadores.get("calefactor") else "Apagado")
            a2.metric("Extractor", "Encendido" if actuadores.get("extractor") else "Apagado")
            a3.metric("Nebulizador", "Encendido" if actuadores.get("nebulizador") else "Apagado")

        except Exception as e:
            st.warning(f"No se pudo obtener el estado actual: {e}")

    with tabs[1]:
        variable = st.selectbox("Variable", ["temperatura", "humedad", "co2"])
        limite = st.slider("Cantidad de registros", min_value=50, max_value=1000, value=200, step=50)

        historial = get_historial_ambiente(ambiente_id, variable=variable, limite=limite)

        if not historial:
            st.info("No hay historial disponible para esta variable.")
        else:
            df = pd.DataFrame(historial)
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
            df = df.dropna(subset=["timestamp"]).sort_values("timestamp")

            if variable not in df.columns:
                st.warning(f"La respuesta no contiene la columna {variable}.")
            else:
                df = df.dropna(subset=[variable])
                columnas = [c for c in ["timestamp", "sensor_id", variable] if c in df.columns]
                st.dataframe(df[columnas], use_container_width=True)

                unidad = {
                    "temperatura": "Temperatura (°C)",
                    "humedad": "Humedad (%)",
                    "co2": "CO₂ (ppm)",
                }[variable]

                fig = plot_variable(
                    df=df,
                    x="timestamp",
                    y=variable,
                    title=f"{variable.capitalize()} del ambiente {ambiente_id}",
                    y_label=unidad,
                )
                st.plotly_chart(fig, use_container_width=True)

    with tabs[2]:
        try:
            estado = get_estado_ambiente(ambiente_id)
            st.json(estado.get("actuadores", {}))
        except Exception as e:
            st.error(f"No se pudo cargar actuadores: {e}")

except Exception as e:
    st.error(f"Error general en la página de ambientes: {e}")
