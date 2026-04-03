import pandas as pd
import streamlit as st
import plotly.express as px

from api.client import get_historial_global
from components.header import render_header

st.set_page_config(page_title="Estadísticas", layout="wide")
render_header("Estadísticas Globales del Sistema")


def porcentaje_en_rango(serie, minimo=None, maximo=None):
    serie = pd.to_numeric(serie, errors="coerce").dropna()
    if serie.empty:
        return None

    condicion = pd.Series(True, index=serie.index)

    if minimo is not None:
        condicion &= serie >= minimo
    if maximo is not None:
        condicion &= serie <= maximo

    return round(condicion.mean() * 100, 2)


try:
    # =========================
    # Filtros principales
    # =========================
    col1, col2, col3 = st.columns([1.4, 1, 1])

    with col1:
        limite = st.slider(
            "Cantidad de registros a analizar",
            min_value=100,
            max_value=5000,
            value=500,
            step=100
        )

    historial = get_historial_global(limite=limite)

    if not historial:
        st.warning("No existen registros históricos disponibles.")
        st.stop()

    df = pd.DataFrame(historial)

    if df.empty:
        st.warning("No se recibieron datos válidos del backend.")
        st.stop()

    # =========================
    # Limpieza de datos
    # =========================
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    for col in ["temperatura", "humedad", "co2"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "ambiente_id" not in df.columns:
        df["ambiente_id"] = "N/A"

    if "sensor_id" not in df.columns:
        df["sensor_id"] = "N/A"

    if "estado_sensor" not in df.columns:
        df["estado_sensor"] = "DESCONOCIDO"

    df["ambiente_id"] = df["ambiente_id"].astype(str)
    df["sensor_id"] = df["sensor_id"].astype(str)
    df["estado_sensor"] = df["estado_sensor"].fillna("DESCONOCIDO").astype(str)

    # =========================
    # Filtros secundarios
    # =========================
    colf1, colf2 = st.columns(2)

    with colf1:
        ambientes = ["Todos"] + sorted(df["ambiente_id"].dropna().unique().tolist())
        ambiente_sel = st.selectbox("Filtrar por ambiente", ambientes)

    with colf2:
        sensores = ["Todos"] + sorted(df["sensor_id"].dropna().unique().tolist())
        sensor_sel = st.selectbox("Filtrar por sensor", sensores)

    if ambiente_sel != "Todos":
        df = df[df["ambiente_id"] == ambiente_sel].copy()

    if sensor_sel != "Todos":
        df = df[df["sensor_id"] == sensor_sel].copy()

    if df.empty:
        st.warning("No hay registros disponibles para los filtros seleccionados.")
        st.stop()

    # =========================
    # KPIs principales
    # =========================
    total_registros = len(df)
    total_ambientes = df["ambiente_id"].nunique()
    total_sensores = df["sensor_id"].nunique()

    if "timestamp" in df.columns and df["timestamp"].notna().any():
        ultima_lectura = df["timestamp"].max().strftime("%Y-%m-%d %H:%M:%S")
    else:
        ultima_lectura = "No disponible"

    porcentaje_ok = None
    if "estado_sensor" in df.columns and not df["estado_sensor"].empty:
        porcentaje_ok = round((df["estado_sensor"].str.upper() == "OK").mean() * 100, 2)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Registros analizados", total_registros)
    k2.metric("Ambientes detectados", total_ambientes)
    k3.metric("Sensores detectados", total_sensores)
    k4.metric("Sensores en estado OK (%)", porcentaje_ok if porcentaje_ok is not None else "N/D")

    st.caption(f"Última lectura registrada: {ultima_lectura}")

    # =========================
    # Resumen estadístico
    # =========================
    st.subheader("Resumen estadístico de variables")

    variables_numericas = [v for v in ["temperatura", "humedad", "co2"] if v in df.columns]

    if not variables_numericas:
        st.warning("No se encontraron variables numéricas disponibles en los registros.")
        st.stop()

    resumen_data = []

    rangos_operacion = {
        "temperatura": (18, 22),
        "humedad": (85, 95),
        "co2": (None, 1000),
    }

    for v in variables_numericas:
        serie = df[v].dropna()

        if serie.empty:
            resumen_data.append({
                "Variable": v,
                "Mínimo": None,
                "Promedio": None,
                "Máximo": None,
                "Desv. estándar": None,
                "Registros válidos": 0,
                "% válidos": 0,
                "% dentro de rango": None,
            })
            continue

        minimo_rango, maximo_rango = rangos_operacion.get(v, (None, None))

        resumen_data.append({
            "Variable": v,
            "Mínimo": round(serie.min(), 2),
            "Promedio": round(serie.mean(), 2),
            "Máximo": round(serie.max(), 2),
            "Desv. estándar": round(serie.std(), 2) if len(serie) > 1 else 0,
            "Registros válidos": int(serie.shape[0]),
            "% válidos": round((serie.shape[0] / len(df)) * 100, 2),
            "% dentro de rango": porcentaje_en_rango(serie, minimo_rango, maximo_rango),
        })

    resumen = pd.DataFrame(resumen_data)
    st.dataframe(resumen, use_container_width=True)

    # =========================
    # Gráficos
    # =========================
    colg1, colg2 = st.columns(2)

    with colg1:
        st.subheader("Registros por ambiente")
        conteo_ambientes = df["ambiente_id"].value_counts().reset_index()
        conteo_ambientes.columns = ["ambiente_id", "cantidad"]

        fig_amb = px.bar(
            conteo_ambientes,
            x="ambiente_id",
            y="cantidad",
            text="cantidad",
            labels={"ambiente_id": "Ambiente", "cantidad": "Cantidad de registros"},
            title="Distribución de registros por ambiente"
        )
        fig_amb.update_layout(height=400)
        st.plotly_chart(fig_amb, use_container_width=True)

    with colg2:
        st.subheader("Estado de sensores")
        conteo_estado = df["estado_sensor"].value_counts().reset_index()
        conteo_estado.columns = ["estado_sensor", "cantidad"]

        fig_estado = px.bar(
            conteo_estado,
            x="estado_sensor",
            y="cantidad",
            text="cantidad",
            labels={"estado_sensor": "Estado del sensor", "cantidad": "Cantidad"},
            title="Distribución del estado de sensores"
        )
        fig_estado.update_layout(height=400)
        st.plotly_chart(fig_estado, use_container_width=True)

    # =========================
    # Cumplimiento operativo
    # =========================
    st.subheader("Cumplimiento respecto a rangos operativos")

    cumplimiento_cols = st.columns(3)

    if "temperatura" in df.columns:
        temp_pct = porcentaje_en_rango(df["temperatura"], 18, 22)
        cumplimiento_cols[0].metric("Temperatura en rango (%)", temp_pct if temp_pct is not None else "N/D")

    if "humedad" in df.columns:
        hum_pct = porcentaje_en_rango(df["humedad"], 85, 95)
        cumplimiento_cols[1].metric("Humedad en rango (%)", hum_pct if hum_pct is not None else "N/D")

    if "co2" in df.columns:
        co2_pct = porcentaje_en_rango(df["co2"], None, 1000)
        cumplimiento_cols[2].metric("CO₂ bajo umbral (%)", co2_pct if co2_pct is not None else "N/D")

    # =========================
    # Tabla detallada
    # =========================
    with st.expander("Ver registros detallados"):
        columnas_visibles = [
            col for col in [
                "timestamp", "ambiente_id", "sensor_id",
                "temperatura", "humedad", "co2", "estado_sensor"
            ]
            if col in df.columns
        ]
        st.dataframe(
            df[columnas_visibles].sort_values("timestamp", ascending=False),
            use_container_width=True
        )

except Exception as e:
    st.error(f"Error al cargar las estadísticas: {e}")