import pandas as pd
import streamlit as st

from api.client import (
    get_ambiente,
    get_ambientes,
    get_estado_ambiente,
    get_historial_ambiente,
)
from components.charts import plot_variable
from components.header import render_header

st.set_page_config(page_title="Ambientes", layout="wide")
render_header("Supervisión por Ambiente")

# =========================================================
# Cambio 11: get_estado_ambiente se llama UNA sola vez y el resultado
# se guarda en session_state. Las pestañas "Resumen" y "Actuadores"
# lo comparten sin hacer un segundo request al backend.
#
# Problema original: Streamlit re-ejecuta el script completo en cada
# interacción. Las dos pestañas llamaban a get_estado_ambiente()
# de forma independiente, duplicando el request en cada cambio de pestaña.
# =========================================================

try:
    ambientes = get_ambientes()

    if not ambientes:
        st.warning("No existen ambientes registrados.")
        st.stop()

    opciones = {f"{a['nombre']} ({a['ambiente_id']})": a["ambiente_id"] for a in ambientes}
    seleccionado = st.selectbox("Selecciona un ambiente", list(opciones.keys()))
    ambiente_id = opciones[seleccionado]

    # Cambio 12: invalidar el cache de estado cuando cambia el ambiente seleccionado
    if st.session_state.get("_ambiente_id_cache") != ambiente_id:
        st.session_state["_ambiente_id_cache"] = ambiente_id
        st.session_state.pop("_estado_cache", None)

    info = get_ambiente(ambiente_id)

    st.subheader("Información del ambiente")
    col1, col2, col3 = st.columns(3)
    col1.metric("Ambiente ID", info["ambiente_id"])
    col2.metric("Nombre", info["nombre"])
    col3.metric("Tipo", info.get("tipo") or "No definido")

    tabs = st.tabs(["Resumen", "Historial", "Actuadores"])

    # ---- Pestaña Resumen ------------------------------------------------
    with tabs[0]:
        # Cambio 13: se carga el estado aquí y se guarda para reutilizar
        if "_estado_cache" not in st.session_state:
            try:
                st.session_state["_estado_cache"] = get_estado_ambiente(ambiente_id)
            except Exception as e:
                st.session_state["_estado_cache"] = None
                st.warning(f"No se pudo obtener el estado actual: {e}")

        estado = st.session_state.get("_estado_cache")

        if estado:
            sensores = estado.get("sensores", [])
            actuadores = estado.get("actuadores", {})

            if sensores:
                sensor = sensores[0]
                c1, c2, c3, c4 = st.columns(4)
                c1.metric(
                    "Temperatura",
                    f"{sensor['temperatura']} °C" if sensor["temperatura"] is not None else "N/D",
                )
                c2.metric(
                    "Humedad",
                    f"{sensor['humedad']} %" if sensor["humedad"] is not None else "N/D",
                )
                c3.metric(
                    "CO₂",
                    f"{sensor['co2']} ppm" if sensor["co2"] is not None else "N/D",
                )
                c4.metric("Estado sensor", sensor.get("estado_sensor") or "DESCONOCIDO")

                if len(sensores) > 1:
                    st.caption(
                        f"Sensores reportando: {len(sensores)}. Se muestra el primero para el resumen."
                    )
            else:
                st.info("Este ambiente aún no tiene sensores reportando.")

            st.markdown("### Estado de actuadores")
            a1, a2, a3 = st.columns(3)
            a1.metric("Calefactor", "Encendido" if actuadores.get("calefactor") else "Apagado")
            a2.metric("Extractor", "Encendido" if actuadores.get("extractor") else "Apagado")
            a3.metric("Nebulizador", "Encendido" if actuadores.get("nebulizador") else "Apagado")

        # Cambio 14: botón explícito para refrescar el estado actual.
        # Evita que Streamlit reconsulte en cada interacción del usuario con
        # cualquier widget de la página (como el selectbox de variable).
        if st.button("🔄 Actualizar estado"):
            st.session_state.pop("_estado_cache", None)
            st.rerun()

    # ---- Pestaña Historial ---------------------------------------------
    with tabs[1]:
        variable = st.selectbox("Variable", ["temperatura", "humedad", "co2"])

        # Cambio 15: el límite por defecto es 200, no 1000.
        # El slider ahora va de 50 a 500 en lugar de 50 a 1000.
        # La mayoría de los usuarios no necesita más de 200 registros para
        # visualizar una tendencia, y cada 100 registros extra son ~100 ms
        # adicionales de query en producción.
        limite = st.slider(
            "Cantidad de registros",
            min_value=50,
            max_value=500,
            value=200,
            step=50,
        )

        # Cambio 16: cache del historial con clave derivada de los parámetros.
        # Si el usuario no cambia la variable ni el límite, no se rehace la
        # petición al backend cuando Streamlit re-ejecuta el script por otra
        # interacción en la misma página (ej: cambiar de pestaña).
        cache_key = f"_historial_{ambiente_id}_{variable}_{limite}"
        if cache_key not in st.session_state:
            with st.spinner("Cargando historial..."):
                st.session_state[cache_key] = get_historial_ambiente(
                    ambiente_id, variable=variable, limite=limite
                )

        historial = st.session_state[cache_key]

        # Botón para forzar recarga
        if st.button("🔄 Recargar historial"):
            st.session_state.pop(cache_key, None)
            st.rerun()

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

    # ---- Pestaña Actuadores --------------------------------------------
    with tabs[2]:
        # Cambio 17: reutiliza el estado cacheado en session_state.
        # El original llamaba a get_estado_ambiente() de nuevo aquí, generando
        # un segundo request idéntico al de la pestaña Resumen.
        estado = st.session_state.get("_estado_cache")
        if estado:
            st.json(estado.get("actuadores", {}))
        else:
            st.info("El estado de actuadores no está disponible. Visita la pestaña Resumen primero.")

except Exception as e:
    st.error(f"Error general en la página de ambientes: {e}")
