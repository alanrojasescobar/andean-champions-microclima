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
# Íconos SVG y tema visual HMI
# =========================================================
SVG_ICONS = {
    "overview": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>""",
    "sensor": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v6"/><path d="M12 16v6"/><path d="M4.93 4.93l4.24 4.24"/><path d="M14.83 14.83l4.24 4.24"/><path d="M2 12h6"/><path d="M16 12h6"/><circle cx="12" cy="12" r="4"/></svg>""",
    "clock": """<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>""",
    "history": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v5h5"/><path d="M3.05 13A9 9 0 1 0 6 5.3L3 8"/><path d="M12 7v5l3 2"/></svg>""",
    "plug": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22v-5"/><path d="M9 8V2"/><path d="M15 8V2"/><path d="M18 8H6l1 7a5 5 0 0 0 10 0z"/></svg>""",
    "chart": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>""",
    "check": """<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>""",
    "warn": """<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>""",
    "temperature": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z"/></svg>""",
    "humidity": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>""",
    "co2": """<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M8 12h8M12 8v8"/></svg>""",
}


def apply_hmi_theme() -> None:
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
            --c-text-muted:  #66746A;
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
            --c-neutral-bg:  #F3F5F0;
            --c-accent:      #1F5B3A;
            --radius-md: 10px;
            --radius-lg: 14px;
            --shadow-sm: 0 1px 3px rgba(31, 91, 58, 0.08), 0 1px 2px rgba(0,0,0,0.04);
        }

        [data-testid="stAppViewContainer"] { background: var(--c-bg); }
        [data-testid="stHeader"] { background: rgba(233, 237, 241, 0.01); }
        .block-container { background: transparent; padding-top: 1.5rem !important; }

        div[data-testid="stVerticalBlockBorderWrapper"][style*="border"] {
            background: var(--c-surface) !important;
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
        .hmi-section-heading svg { opacity: 0.65; }

        .hmi-muted {
            color: var(--c-text-muted);
            font-size: 0.80rem;
            display: flex;
            align-items: center;
            gap: 0.35rem;
        }

        .hmi-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.25rem;
            padding: 0.2rem 0.6rem;
            border-radius: 999px;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.03em;
            border: 1px solid transparent;
            vertical-align: middle;
        }
        .hmi-badge-ok { background: var(--c-ok-pill); color: var(--c-ok); border-color: var(--c-ok-border); }
        .hmi-badge-warn { background: var(--c-warn-pill); color: var(--c-warn); border-color: var(--c-warn-border); }
        .hmi-badge-alert { background: var(--c-alert-pill); color: var(--c-alert); border-color: var(--c-alert-border); }

        [data-testid="stMetric"] {
            background: var(--c-neutral-bg);
            border: 1px solid var(--c-border);
            border-radius: var(--radius-md);
            padding: 0.65rem 0.85rem 0.55rem;
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.68rem !important;
            color: var(--c-text-sub) !important;
            font-weight: 700 !important;
            text-transform: uppercase;
            letter-spacing: 0.06em;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.45rem !important;
            color: var(--c-text-main) !important;
            font-weight: 800 !important;
        }

        .hmi-act-card {
            border: 1.5px solid var(--c-border);
            border-radius: var(--radius-md);
            padding: 0.85rem 0.55rem 0.75rem;
            text-align: center;
            background: var(--c-neutral-bg);
            box-shadow: var(--shadow-sm);
        }
        .hmi-act-card.on { border-color: var(--c-ok-border); background: var(--c-ok-bg); }
        .hmi-act-card.off { border-color: var(--c-border); background: #F8FAF7; }
        .hmi-pilot { width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-bottom: 0.35rem; }
        .hmi-pilot.on { background: #22C55E; box-shadow: 0 0 0 3px #22C55E28, 0 0 8px #22C55E66; }
        .hmi-pilot.off { background: #CBD5E1; }
        .hmi-act-icon { color: var(--c-accent); opacity: 0.65; margin-bottom: 0.25rem; }
        .hmi-act-name { font-size: 0.70rem; font-weight: 800; color: var(--c-text-main); display:block; }
        .hmi-act-state { font-size: 0.65rem; color: var(--c-text-sub); display:block; margin-top:0.15rem; }

        div[data-baseweb="select"] > div { border-color: var(--c-border) !important; background: #FFFFFF !important; }
        .stButton > button {
            border-radius: 999px;
            border: 1px solid var(--c-border);
            background: #FFFFFF;
            color: var(--c-text-main);
            font-weight: 700;
        }
        .stButton > button:hover { border-color: var(--c-accent); color: var(--c-accent); }

        button[data-baseweb="tab"] {
            font-weight: 800 !important;
            color: var(--c-text-sub) !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            color: var(--c-accent) !important;
        }

        [data-testid="stDataFrame"] { border: 1px solid var(--c-border); border-radius: var(--radius-md); overflow: hidden; }
        hr[data-testid="stDivider"] { border-color: var(--c-border) !important; margin: 0.6rem 0 !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hmi_heading(icon_key: str, text: str) -> None:
    st.markdown(
        f'<div class="hmi-section-heading">{SVG_ICONS.get(icon_key, "")} {text}</div>',
        unsafe_allow_html=True,
    )


def status_badge(text: str, kind: str = "ok") -> str:
    cls = {"ok": "hmi-badge-ok", "warn": "hmi-badge-warn", "alert": "hmi-badge-alert"}.get(kind, "hmi-badge-ok")
    icon = SVG_ICONS["check"] if kind == "ok" else SVG_ICONS["warn"]
    return f'<span class="hmi-badge {cls}">{icon}{text}</span>'


def actuator_card(nombre: str, activo: bool, icon_key: str) -> str:
    state_cls = "on" if activo else "off"
    pilot_cls = "on" if activo else "off"
    estado = "Encendido" if activo else "Apagado"
    comando = "Salida activada" if activo else "Salida desactivada"
    return f"""
    <div class="hmi-act-card {state_cls}">
        <span class="hmi-pilot {pilot_cls}"></span>
        <div class="hmi-act-icon">{SVG_ICONS.get(icon_key, "")}</div>
        <span class="hmi-act-name">{nombre}</span>
        <span class="hmi-act-state">{estado}</span>
        <span class="hmi-act-state">{comando}</span>
    </div>
    """


apply_hmi_theme()

# =========================================================
# Lógica principal
# =========================================================
try:
    ambientes = get_ambientes()

    if not ambientes:
        st.warning("No existen ambientes registrados.")
        st.stop()

    opciones = {f"{a['nombre']} ({a['ambiente_id']})": a["ambiente_id"] for a in ambientes}

    with st.container(border=True):
        hmi_heading("overview", "Selección de ambiente")
        c_sel, c_time = st.columns([2, 1])
        with c_sel:
            seleccionado = st.selectbox("Selecciona un ambiente", list(opciones.keys()))
        with c_time:
            st.markdown(
                f'<div class="hmi-muted" style="justify-content:flex-end; margin-top:1.8rem">{SVG_ICONS["clock"]} Actualizado: {pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")}</div>',
                unsafe_allow_html=True,
            )

    ambiente_id = opciones[seleccionado]

    # Invalidar cache cuando cambia el ambiente seleccionado
    if st.session_state.get("_ambiente_id_cache") != ambiente_id:
        st.session_state["_ambiente_id_cache"] = ambiente_id
        st.session_state.pop("_estado_cache", None)

    info = get_ambiente(ambiente_id)

    with st.container(border=True):
        hmi_heading("sensor", "Información del ambiente")
        col1, col2, col3 = st.columns(3)
        col1.metric("Ambiente ID", info["ambiente_id"])
        col2.metric("Nombre", info["nombre"])
        col3.metric("Tipo", info.get("tipo") or "No definido")

    tabs = st.tabs(["Resumen", "Historial", "Actuadores"])

    # ---- Pestaña Resumen ------------------------------------------------
    with tabs[0]:
        if "_estado_cache" not in st.session_state:
            try:
                st.session_state["_estado_cache"] = get_estado_ambiente(ambiente_id)
            except Exception as e:
                st.session_state["_estado_cache"] = None
                st.warning(f"No se pudo obtener el estado actual: {e}")

        estado = st.session_state.get("_estado_cache")

        with st.container(border=True):
            hmi_heading("overview", "Resumen operativo")

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
                    estado_sensor = sensor.get("estado_sensor") or "DESCONOCIDO"
                    c4.metric("Estado sensor", estado_sensor)

                    if len(sensores) > 1:
                        st.markdown(
                            f'<div class="hmi-muted" style="margin-top:0.5rem">Sensores reportando: <b>{len(sensores)}</b>. Se muestra el primero para el resumen.</div>',
                            unsafe_allow_html=True,
                        )
                else:
                    st.info("Este ambiente aún no tiene sensores reportando.")

                st.write("")
                hmi_heading("plug", "Estado de actuadores")
                a1, a2, a3 = st.columns(3)
                with a1:
                    st.markdown(actuator_card("Calefactor", bool(actuadores.get("calefactor")), "temperature"), unsafe_allow_html=True)
                with a2:
                    st.markdown(actuator_card("Extractor", bool(actuadores.get("extractor")), "plug"), unsafe_allow_html=True)
                with a3:
                    st.markdown(actuator_card("Nebulizador", bool(actuadores.get("nebulizador")), "humidity"), unsafe_allow_html=True)
            else:
                st.info("El estado actual no está disponible.")

            if st.button("Actualizar estado"):
                st.session_state.pop("_estado_cache", None)
                st.rerun()

    # ---- Pestaña Historial ---------------------------------------------
    with tabs[1]:
        with st.container(border=True):
            hmi_heading("history", "Historial de mediciones")
            f1, f2 = st.columns([1, 1])
            with f1:
                variable = st.selectbox("Variable", ["temperatura", "humedad", "co2"])
            with f2:
                limite = st.slider(
                    "Cantidad de registros",
                    min_value=50,
                    max_value=500,
                    value=200,
                    step=50,
                )

            cache_key = f"_historial_{ambiente_id}_{variable}_{limite}"
            if cache_key not in st.session_state:
                with st.spinner("Cargando historial..."):
                    st.session_state[cache_key] = get_historial_ambiente(
                        ambiente_id, variable=variable, limite=limite
                    )

            historial = st.session_state[cache_key]

            if st.button("Recargar historial"):
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

                    hmi_heading("chart", "Tabla de registros")
                    st.dataframe(df[columnas], use_container_width=True, hide_index=True)

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
        estado = st.session_state.get("_estado_cache")
        with st.container(border=True):
            hmi_heading("plug", "Detalle de actuadores")
            if estado:
                actuadores = estado.get("actuadores", {})
                a1, a2, a3 = st.columns(3)
                with a1:
                    st.markdown(actuator_card("Calefactor", bool(actuadores.get("calefactor")), "temperature"), unsafe_allow_html=True)
                with a2:
                    st.markdown(actuator_card("Extractor", bool(actuadores.get("extractor")), "plug"), unsafe_allow_html=True)
                with a3:
                    st.markdown(actuator_card("Nebulizador", bool(actuadores.get("nebulizador")), "humidity"), unsafe_allow_html=True)

                with st.expander("Ver JSON del backend"):
                    st.json(actuadores)
            else:
                st.info("El estado de actuadores no está disponible. Visita la pestaña Resumen primero.")

except Exception as e:
    st.error(f"Error general en la página de ambientes: {e}")
