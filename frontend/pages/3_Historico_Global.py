import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from typing import Optional

from api.client import get_historial_global
from components.header import render_header

st.set_page_config(page_title="Histórico Global", layout="wide")
render_header("Histórico Global del Sistema")


# =========================================================
# Configuración
# =========================================================
UNIDADES = {
    "temperatura": "Temperatura (°C)",
    "humedad": "Humedad (%)",
    "co2": "CO₂ (ppm)",
}

RANGOS = {
    "temperatura": (18, 22),
    "humedad": (85, 95),
    "co2": (None, 1000),
}

FRECUENCIAS = {
    "Sin agrupar": None,
    "10 s": "10s",
    "30 s": "30s",
    "1 min": "1min",
    "5 min": "5min",
}


# =========================================================
# Utilidades
# =========================================================
def preparar_dataframe(historial: list) -> pd.DataFrame:
    df = pd.DataFrame(historial)

    if "timestamp" not in df.columns:
        raise ValueError("La respuesta del backend no contiene la columna 'timestamp'.")

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

    df = df.dropna(subset=["timestamp"]).sort_values("timestamp").copy()
    df["serie"] = "Ambiente " + df["ambiente_id"] + " · Sensor " + df["sensor_id"]

    return df


def porcentaje_en_rango(serie: pd.Series, variable: str):
    serie = pd.to_numeric(serie, errors="coerce").dropna()
    if serie.empty or variable not in RANGOS:
        return None

    minimo, maximo = RANGOS[variable]
    mask = pd.Series(True, index=serie.index)

    if minimo is not None:
        mask &= serie >= minimo
    if maximo is not None:
        mask &= serie <= maximo

    return round(mask.mean() * 100, 2)


def construir_resumen_global(df: pd.DataFrame, variable: str) -> pd.DataFrame:
    base = df[["timestamp", variable]].dropna().copy()
    base["bucket"] = base["timestamp"].dt.floor("1s")

    resumen = (
        base.groupby("bucket")[variable]
        .agg(promedio="mean", minimo="min", maximo="max", cantidad="count")
        .reset_index()
        .rename(columns={"bucket": "timestamp"})
    )

    return resumen


def reamostrar_por_sensor(df: pd.DataFrame, variable: str, frecuencia: Optional[str]) -> pd.DataFrame:
    if frecuencia is None:
        return df.dropna(subset=[variable]).copy()
    

    partes = []
    for serie, grupo in df.groupby("serie"):
        g = grupo.sort_values("timestamp").set_index("timestamp")
        agg = g[[variable]].resample(frecuencia).mean().dropna().reset_index()
        agg["serie"] = serie
        partes.append(agg)

    if not partes:
        return pd.DataFrame(columns=["timestamp", variable, "serie"])

    return pd.concat(partes, ignore_index=True)


def construir_global(df: pd.DataFrame, variable: str, frecuencia: Optional[str]) -> pd.DataFrame:
    base = df[["timestamp", variable]].dropna().copy().sort_values("timestamp")

    if frecuencia is None:
        base["bucket"] = base["timestamp"].dt.floor("1s")
    else:
        base["bucket"] = base["timestamp"].dt.floor(frecuencia)

    agg = (
        base.groupby("bucket")[variable]
        .agg(promedio="mean", minimo="min", maximo="max", cantidad="count")
        .reset_index()
        .rename(columns={"bucket": "timestamp"})
    )

    return agg


def plot_por_sensor(df_plot: pd.DataFrame, variable: str, unidad: str):
    fig = go.Figure()

    for serie, grupo in df_plot.groupby("serie"):
        grupo = grupo.sort_values("timestamp")
        fig.add_trace(
            go.Scatter(
                x=grupo["timestamp"],
                y=grupo[variable],
                mode="lines+markers",
                name=serie,
                connectgaps=False,
                marker=dict(size=5),
                line=dict(width=2),
                hovertemplate=(
                    "<b>%{fullData.name}</b><br>"
                    "Fecha: %{x}<br>"
                    + unidad +
                    ": %{y:.2f}<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        title=f"{variable.capitalize()} por sensor",
        xaxis_title="Tiempo",
        yaxis_title=unidad,
        hovermode="x unified",
        legend_title="Series",
        height=520,
        margin=dict(l=20, r=20, t=60, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    return fig


def plot_global(df_global: pd.DataFrame, variable: str, unidad: str, mostrar_banda: bool):
    fig = go.Figure()

    if mostrar_banda:
        fig.add_trace(
            go.Scatter(
                x=df_global["timestamp"],
                y=df_global["maximo"],
                mode="lines",
                line=dict(width=0),
                showlegend=False,
                hoverinfo="skip",
                name="Máximo",
            )
        )

        fig.add_trace(
            go.Scatter(
                x=df_global["timestamp"],
                y=df_global["minimo"],
                mode="lines",
                fill="tonexty",
                line=dict(width=0),
                name="Rango min-max",
                hovertemplate="Mínimo: %{y:.2f}<extra></extra>",
            )
        )

    fig.add_trace(
        go.Scatter(
            x=df_global["timestamp"],
            y=df_global["promedio"],
            mode="lines+markers",
            name="Promedio global",
            line=dict(width=3),
            marker=dict(size=5),
            hovertemplate=(
                "<b>Promedio global</b><br>"
                "Fecha: %{x}<br>"
                + unidad +
                ": %{y:.2f}<extra></extra>"
            ),
        )
    )

    titulo = f"{variable.capitalize()} global del sistema"
    if mostrar_banda:
        titulo += " (promedio + rango)"

    fig.update_layout(
        title=titulo,
        xaxis_title="Tiempo",
        yaxis_title=unidad,
        hovermode="x unified",
        height=520,
        margin=dict(l=20, r=20, t=60, b=20),
    )

    return fig


# =========================================================
# UI principal
# =========================================================
try:
    c1, c2, c3, c4 = st.columns([1.2, 1, 1.15, 1])

    with c1:
        variable = st.selectbox(
            "Variable",
            ["temperatura", "humedad", "co2"],
            index=0
        )

    with c2:
        limite = st.slider(
            "Cantidad de registros",
            min_value=100,
            max_value=5000,
            value=500,
            step=100
        )

    with c3:
        vista = st.selectbox(
            "Tipo de visualización",
            ["Por sensor", "Promedio global", "Promedio + banda"],
            index=2
        )

    with c4:
        frecuencia_label = st.selectbox(
            "Agrupación temporal",
            list(FRECUENCIAS.keys()),
            index=2
        )

    historial = get_historial_global(variable=variable, limite=limite)

    if not historial:
        st.warning("No existen registros históricos para la consulta realizada.")
        st.stop()

    df = preparar_dataframe(historial)

    if variable not in df.columns:
        st.error(f"La respuesta del backend no contiene la variable '{variable}'.")
        st.stop()

    df = df.dropna(subset=[variable]).copy()

    if df.empty:
        st.warning("No hay datos válidos para la variable seleccionada.")
        st.stop()

    f1, f2 = st.columns(2)

    with f1:
        ambientes = ["Todos"] + sorted(df["ambiente_id"].unique().tolist())
        ambiente_sel = st.selectbox("Filtrar por ambiente", ambientes)

    with f2:
        sensores_disponibles = df["sensor_id"].unique().tolist()
        sensores_disponibles = ["Todos"] + sorted(map(str, sensores_disponibles))
        sensor_sel = st.selectbox("Filtrar por sensor", sensores_disponibles)

    if ambiente_sel != "Todos":
        df = df[df["ambiente_id"] == ambiente_sel].copy()

    if sensor_sel != "Todos":
        df = df[df["sensor_id"] == sensor_sel].copy()

    if df.empty:
        st.warning("No hay datos válidos para los filtros seleccionados.")
        st.stop()

    ultima_lectura = df["timestamp"].max()
    porcentaje_rango = porcentaje_en_rango(df[variable], variable)
    sensores_activos = df["serie"].nunique()

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Registros", len(df))
    k2.metric("Sensores visibles", sensores_activos)
    k3.metric("Mínimo", round(df[variable].min(), 2))
    k4.metric("Promedio", round(df[variable].mean(), 2))
    k5.metric("Máximo", round(df[variable].max(), 2))

    s1, s2 = st.columns([1.2, 2])

    with s1:
        if porcentaje_rango is not None:
            st.metric("% en rango", porcentaje_rango)
        else:
            st.metric("% en rango", "N/D")

    with s2:
        st.caption(
            f"Última lectura: {ultima_lectura.strftime('%Y-%m-%d %H:%M:%S')} | "
            f"Rango objetivo para {variable}: {RANGOS[variable]}"
        )

    frecuencia = FRECUENCIAS[frecuencia_label]

    if vista == "Por sensor":
        df_plot = reamostrar_por_sensor(df, variable, frecuencia)
        fig = plot_por_sensor(df_plot, variable, UNIDADES[variable])
    else:
        df_global = construir_global(df, variable, frecuencia)
        fig = plot_global(
            df_global=df_global,
            variable=variable,
            unidad=UNIDADES[variable],
            mostrar_banda=(vista == "Promedio + banda"),
        )

    st.plotly_chart(fig, use_container_width=True)

    tab1, tab2, tab3 = st.tabs(["Resumen", "Distribución", "Detalle"])

    with tab1:
        resumen = pd.DataFrame(
            {
                "variable": [variable],
                "mínimo": [round(df[variable].min(), 2)],
                "promedio": [round(df[variable].mean(), 2)],
                "máximo": [round(df[variable].max(), 2)],
                "desv_est": [round(df[variable].std(), 2) if len(df[variable].dropna()) > 1 else 0],
                "registros_válidos": [int(df[variable].dropna().shape[0])],
                "%_en_rango": [porcentaje_rango],
            }
        )
        st.dataframe(resumen, use_container_width=True, hide_index=True)

    with tab2:
        c5, c6 = st.columns(2)

        with c5:
            st.subheader("Registros por ambiente")
            conteo_ambientes = df["ambiente_id"].value_counts().reset_index()
            conteo_ambientes.columns = ["ambiente_id", "cantidad"]
            st.dataframe(conteo_ambientes, use_container_width=True, hide_index=True)

        with c6:
            st.subheader("Registros por sensor")
            conteo_sensores = df["serie"].value_counts().reset_index()
            conteo_sensores.columns = ["sensor", "cantidad"]
            st.dataframe(conteo_sensores, use_container_width=True, hide_index=True)

    with tab3:
        columnas_detalle = [
            col for col in ["timestamp", "ambiente_id", "sensor_id", variable, "estado_sensor"]
            if col in df.columns
        ]
        st.dataframe(
            df[columnas_detalle].sort_values("timestamp", ascending=False),
            use_container_width=True,
            hide_index=True
        )

except Exception as e:
    st.error(f"Error al cargar el histórico global: {e}")