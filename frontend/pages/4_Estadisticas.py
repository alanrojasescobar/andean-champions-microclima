import pandas as pd
import streamlit as st
import plotly.express as px

from api.client import get_historial_global
from components.header import render_header

st.set_page_config(page_title="Estadísticas", layout="wide")
render_header("Estadísticas Globales del Sistema")


# =========================================================
# Íconos SVG — estilo HMI sin emojis
# =========================================================
SVG_ICONS = {
    "overview": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>""",
    "filter": """<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>""",
    "chart": """<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>""",
    "table": """<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/><line x1="9" y1="3" x2="9" y2="21"/><line x1="15" y1="3" x2="15" y2="21"/></svg>""",
    "check": """<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>""",
    "clock": """<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>""",
}


# =========================================================
# Estilos visuales HMI
# =========================================================
st.markdown(
    """
    <style>
    :root {
        --c-bg:          #E9EDF1;
        --c-surface:     #FFFFFF;
        --c-border:      #D5D9CE;
        --c-border-sub:  #F5F4E0;
        --c-text-main:   #17211A;
        --c-text-sub:    #4B5A4F;
        --c-text-muted:  #17211A;

        --c-ok:          #15803D;
        --c-ok-bg:       #EEF8F0;
        --c-ok-border:   #8FD19E;
        --c-ok-pill:     #DDF3E3;

        --c-warn:        #92400E;
        --c-warn-bg:     #FFF8E7;
        --c-warn-border: #F2C66D;
        --c-warn-pill:   #F8E8B8;

        --c-alert:       #991B1B;
        --c-alert-bg:    #FFF0F0;
        --c-alert-border:#F2A0A0;
        --c-alert-pill:  #F8DADA;

        --c-neutral:     #334155;
        --c-neutral-bg:  #F3F5F0;
        --c-neutral-border:#D5D9CE;
        --c-neutral-pill:#E3E6DD;

        --c-accent:      #1F5B3A;
        --c-accent-light:#E8F3EC;

        --radius-sm: 6px;
        --radius-md: 10px;
        --radius-lg: 14px;
        --shadow-sm: 0 1px 3px rgba(31, 91, 58, 0.08), 0 1px 2px rgba(0,0,0,0.04);
        --shadow-md: 0 4px 12px rgba(31, 91, 58, 0.12), 0 1px 3px rgba(0,0,0,0.05);
    }

    [data-testid="stAppViewContainer"] { background: var(--c-bg); }
    [data-testid="stHeader"] { background: rgba(233, 237, 241, 0.01); }

    .block-container {
        background: transparent;
        padding-top: 1.5rem !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"][style*="border"] {
        background: #FFFFFF !important;
        border-radius: var(--radius-lg) !important;
        box-shadow: var(--shadow-sm) !important;
        border-color: var(--c-border) !important;
    }

    .hmi-section-heading {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 0.75rem;
        font-weight: 800;
        color: var(--c-text-sub);
        text-transform: uppercase;
        letter-spacing: 0.09em;
        margin-bottom: 0.9rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid var(--c-border);
    }
    .hmi-section-heading svg { opacity: 0.65; color: var(--c-accent); }

    .hmi-caption {
        color: var(--c-text-sub);
        font-size: 0.78rem;
        display: flex;
        align-items: center;
        gap: 0.35rem;
        margin-top: 0.35rem;
    }

    .hmi-note {
        background: var(--c-neutral-bg);
        border: 1px solid var(--c-border);
        border-left: 3px solid var(--c-accent);
        border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
        color: var(--c-text-sub);
        font-size: 0.74rem;
        padding: 0.55rem 0.75rem;
        line-height: 1.5;
    }

    [data-testid="stMetric"] {
        background: var(--c-neutral-bg);
        border: 1px solid var(--c-border);
        border-radius: var(--radius-md);
        padding: 0.65rem 0.85rem 0.55rem;
        box-shadow: var(--shadow-sm);
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.68rem !important;
        color: var(--c-text-sub) !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.55rem !important;
        color: var(--c-text-main) !important;
        font-weight: 800 !important;
    }

    [data-testid="stExpander"] {
        border: 1px solid var(--c-border) !important;
        border-radius: var(--radius-md) !important;
        background: var(--c-neutral-bg) !important;
    }

    hr[data-testid="stDivider"] {
        border-color: var(--c-border) !important;
        margin: 0.6rem 0 !important;
    }

    .stSelectbox label, .stSlider label {
        color: var(--c-text-sub) !important;
        font-weight: 700 !important;
        letter-spacing: 0.02em;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# Configuración
# =========================================================
RANGOS_OPERACION = {
    "temperatura": (18, 22),
    "humedad": (85, 95),
    "co2": (None, 1000),
}

NOMBRES_VARIABLES = {
    "temperatura": "Temperatura",
    "humedad": "Humedad relativa",
    "co2": "CO₂",
}

UNIDADES = {
    "temperatura": "°C",
    "humedad": "%",
    "co2": "ppm",
}


# =========================================================
# Utilidades
# =========================================================
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


def hmi_heading(icon_key: str, texto: str):
    st.markdown(
        f'<div class="hmi-section-heading">{SVG_ICONS[icon_key]} {texto}</div>',
        unsafe_allow_html=True,
    )


def aplicar_estilo_figura(fig, titulo: str = ""):
    fig.update_layout(
        title=titulo,
        height=400,
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        font=dict(color="#17211A"),
        margin=dict(l=20, r=20, t=55, b=30),
        xaxis=dict(gridcolor="#E6E8E1", zerolinecolor="#E6E8E1"),
        yaxis=dict(gridcolor="#E6E8E1", zerolinecolor="#E6E8E1"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def formatear_rango(variable: str):
    minimo, maximo = RANGOS_OPERACION.get(variable, (None, None))
    unidad = UNIDADES.get(variable, "")
    if minimo is not None and maximo is not None:
        return f"{minimo}–{maximo} {unidad}"
    if maximo is not None:
        return f"< {maximo} {unidad}"
    return "No definido"


# =========================================================
# UI principal
# =========================================================
try:
    # =========================
    # Filtros principales
    # =========================
    with st.container(border=True):
        hmi_heading("filter", "Filtros de análisis")
        col1, col2, col3 = st.columns([1.4, 1, 1])

        with col1:
            limite = st.slider(
                "Cantidad de registros a analizar",
                min_value=100,
                max_value=5000,
                value=500,
                step=100,
            )

        with col2:
            st.markdown(
                """
                <div class="hmi-note">
                    La consulta analiza los registros históricos más recientes disponibles en la base de datos.
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col3:
            st.markdown(
                """
                <div class="hmi-note">
                    Los porcentajes se calculan respecto a los rangos operativos definidos para fructificación.
                </div>
                """,
                unsafe_allow_html=True,
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
    with st.container(border=True):
        hmi_heading("filter", "Filtros de visualización")
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

    with st.container(border=True):
        hmi_heading("overview", "Indicadores generales")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Registros analizados", total_registros)
        k2.metric("Ambientes detectados", total_ambientes)
        k3.metric("Sensores detectados", total_sensores)
        k4.metric("Sensores OK (%)", porcentaje_ok if porcentaje_ok is not None else "N/D")

        st.markdown(
            f'<div class="hmi-caption">{SVG_ICONS["clock"]} Última lectura registrada: <b>{ultima_lectura}</b></div>',
            unsafe_allow_html=True,
        )

    # =========================
    # Resumen estadístico
    # =========================
    variables_numericas = [v for v in ["temperatura", "humedad", "co2"] if v in df.columns]

    if not variables_numericas:
        st.warning("No se encontraron variables numéricas disponibles en los registros.")
        st.stop()

    resumen_data = []

    for v in variables_numericas:
        serie = df[v].dropna()

        if serie.empty:
            resumen_data.append({
                "Variable": NOMBRES_VARIABLES.get(v, v),
                "Mínimo": None,
                "Promedio": None,
                "Máximo": None,
                "Desv. estándar": None,
                "Registros válidos": 0,
                "% válidos": 0,
                "% dentro de rango": None,
                "Rango operativo": formatear_rango(v),
            })
            continue

        minimo_rango, maximo_rango = RANGOS_OPERACION.get(v, (None, None))

        resumen_data.append({
            "Variable": NOMBRES_VARIABLES.get(v, v),
            "Mínimo": round(serie.min(), 2),
            "Promedio": round(serie.mean(), 2),
            "Máximo": round(serie.max(), 2),
            "Desv. estándar": round(serie.std(), 2) if len(serie) > 1 else 0,
            "Registros válidos": int(serie.shape[0]),
            "% válidos": round((serie.shape[0] / len(df)) * 100, 2),
            "% dentro de rango": porcentaje_en_rango(serie, minimo_rango, maximo_rango),
            "Rango operativo": formatear_rango(v),
        })

    resumen = pd.DataFrame(resumen_data)

    with st.container(border=True):
        hmi_heading("table", "Resumen estadístico de variables")
        st.dataframe(resumen, use_container_width=True, hide_index=True)

    # =========================
    # Gráficos
    # =========================
    colg1, colg2 = st.columns(2)

    with colg1:
        with st.container(border=True):
            hmi_heading("chart", "Registros por ambiente")
            conteo_ambientes = df["ambiente_id"].value_counts().reset_index()
            conteo_ambientes.columns = ["ambiente_id", "cantidad"]

            fig_amb = px.bar(
                conteo_ambientes,
                x="ambiente_id",
                y="cantidad",
                text="cantidad",
                labels={"ambiente_id": "Ambiente", "cantidad": "Cantidad de registros"},
            )
            fig_amb.update_traces(textposition="outside")
            fig_amb = aplicar_estilo_figura(fig_amb, "Distribución de registros por ambiente")
            st.plotly_chart(fig_amb, use_container_width=True)

    with colg2:
        with st.container(border=True):
            hmi_heading("chart", "Estado de sensores")
            conteo_estado = df["estado_sensor"].value_counts().reset_index()
            conteo_estado.columns = ["estado_sensor", "cantidad"]

            fig_estado = px.bar(
                conteo_estado,
                x="estado_sensor",
                y="cantidad",
                text="cantidad",
                labels={"estado_sensor": "Estado del sensor", "cantidad": "Cantidad"},
            )
            fig_estado.update_traces(textposition="outside")
            fig_estado = aplicar_estilo_figura(fig_estado, "Distribución del estado de sensores")
            st.plotly_chart(fig_estado, use_container_width=True)

    # =========================
    # Cumplimiento operativo
    # =========================
    with st.container(border=True):
        hmi_heading("check", "Cumplimiento respecto a rangos operativos")
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

        detalle = df[columnas_visibles].copy()
        if "timestamp" in detalle.columns:
            detalle = detalle.sort_values("timestamp", ascending=False)

        st.dataframe(detalle, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error al cargar las estadísticas: {e}")
