import streamlit as st
import pandas as pd
import base64
from pathlib import Path
from api.client import get_ambientes, get_estados_ambientes
from components.header import render_header

st.set_page_config(page_title="Dashboard", layout="wide")
def cargar_logo_base64(ruta_logo):
    ruta_logo = Path(ruta_logo)

    if not ruta_logo.exists():
        return ""

    with open(ruta_logo, "rb") as img_file:
        logo_b64 = base64.b64encode(img_file.read()).decode()

    return f"data:image/png;base64,{logo_b64}"
# =========================================================
# Logo institucional (esquina superior derecha)
# Reemplaza LOGO_URL con la URL real de tu logo institucional
# =========================================================


render_header("HMI General del Sistema")

# =========================================================
# Íconos SVG — reemplaza todos los emojis
# =========================================================
SVG_ICONS = {
    # Variables de proceso
    "temperatura": """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z"/></svg>""",
    "humedad":     """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>""",
    "co2":         """<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M8 12h8M12 8v8"/></svg>""",
    # Actuadores
    "calefactor":  """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2c0 6-6 6-6 12a6 6 0 0 0 12 0c0-6-6-6-6-12z"/><path d="M12 22v-4"/></svg>""",
    "extractor":   """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 8v8M8 12h8"/></svg>""",
    "nebulizador": """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a7 7 0 0 1 7 7c0 4.5-7 13-7 13S5 13.5 5 9a7 7 0 0 1 7-7z"/><circle cx="12" cy="9" r="2.5"/></svg>""",
    "control":     """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M4.93 4.93a10 10 0 0 0 0 14.14"/></svg>""",
    "sensor":      """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/><path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/></svg>""",
    # Estado
    "estado":      """<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="8"/></svg>""",
    "check":       """<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>""",
    "warn":        """<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>""",
    "critical":    """<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>""",
    "gear":        """<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M4.93 4.93a10 10 0 0 0 0 14.14"/></svg>""",
    "clock":       """<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>""",
    "alarm":       """<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>""",
    "info":        """<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>""",
    "overview":    """<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>""",
    "plug":        """<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22v-5"/><path d="M9 8V2"/><path d="M15 8V2"/><path d="M18 8H6l1 7a5 5 0 0 0 10 0z"/></svg>""",
}

# =========================================================
# Estilos visuales HMI — refinados, sin emojis
# =========================================================
st.markdown(
    """
    <style>
    /* ── Tokens de diseño ──────────────────────────── */
    :root {
        --c-bg:          #E9EDF1;
        --c-surface:     #ffffff;
        --c-border:      #D5D9CE;
        --c-border-sub:  #f5f4e0;
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

        --c-accent:      #f5f4e0;
        --c-accent-light:#d8e8e8;

        --radius-sm: 6px;
        --radius-md: 10px;
        --radius-lg: 14px;
        --shadow-sm: 0 1px 3px rgba(31, 91, 58, 0.08), 0 1px 2px rgba(0,0,0,0.04);
        --shadow-md: 0 4px 12px rgba(31, 91, 58, 0.12), 0 1px 3px rgba(0,0,0,0.05);
    }
    /* Fondo general estilo dashboard profesional */
    [data-testid="stAppViewContainer"] {
        background: var(--c-bg);
    }

    [data-testid="stHeader"] {
        background: rgba(233, 237, 241, 0.01);
    }

    .block-container {
        background: transparent;
        padding-top: 1.5rem !important;
    }

    /* ── Cards de sección: se aplican via clase personalizada ── */
    .hmi-card-wrap {
        background: #FFFFFF;
        border: 1px solid var(--c-border);
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-sm);
        padding: 1.1rem 1.2rem 1rem;
        margin-bottom: 1rem;
    }

    /* st.container(border=True): solo el wrapper que tiene borde real de Streamlit */
    div[data-testid="stVerticalBlockBorderWrapper"][style*="border"] {
        background: #FFFFFF !important;
        border-radius: var(--radius-lg) !important;
        box-shadow: var(--shadow-sm) !important;
        border-color: var(--c-border) !important;
    }

    /* ── Badges ─────────────────────────────────────── */
    .badge {
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
    .badge-ok      { background: var(--c-ok-pill);      color: var(--c-ok);      border-color: var(--c-ok-border); }
    .badge-warn    { background: var(--c-warn-pill);     color: var(--c-warn);    border-color: var(--c-warn-border); }
    .badge-alert   { background: var(--c-alert-pill);    color: var(--c-alert);   border-color: var(--c-alert-border); }
    .badge-neutral { background: var(--c-neutral-pill);  color: var(--c-neutral); border-color: var(--c-neutral-border); }

    /* ── Encabezados de sección ──────────────────────── */
    .section-title {
        display: flex;
        align-items: center;
        gap: 0.4rem;
        font-size: 0.68rem;
        font-weight: 800;
        color: var(--c-text-muted);
        text-transform: uppercase;
        letter-spacing: 0.10em;
        margin: 0.9rem 0 0.5rem 0;
        padding-bottom: 0.35rem;
        border-bottom: 1px solid var(--c-border-sub);
    }
    .section-title svg { flex-shrink: 0; opacity: 0.7; }

    /* ── Barra de ESTADO DEL SISTEMA ─────────────────── */
    .hmi-status-bar {
        display: flex;
        flex-wrap: wrap;
        border: 1px solid var(--c-border);
        border-radius: var(--radius-md);
        overflow: hidden;
        background: var(--c-surface);
        box-shadow: var(--shadow-sm);
        margin-bottom: 0.25rem;
    }
    .hmi-status-cell {
        flex: 1;
        min-width: 100px;
        padding: 0.55rem 0.85rem;
        border-right: 1px solid var(--c-border-sub);
        background: var(--c-surface);
    }
    .hmi-status-cell:last-child { border-right: none; }
    .hmi-status-cell:first-child { background: var(--c-neutral-bg); }
    .hmi-status-label {
        font-size: 0.60rem;
        font-weight: 700;
        color: var(--c-text-muted);
        text-transform: uppercase;
        letter-spacing: 0.07em;
    }
    .hmi-status-value {
        font-size: 0.80rem;
        font-weight: 700;
        margin-top: 0.1rem;
        white-space: nowrap;
        display: flex;
        align-items: center;
        gap: 0.3rem;
    }
    .hmi-ok      { color: var(--c-ok); }
    .hmi-warn    { color: var(--c-warn); }
    .hmi-alert   { color: var(--c-alert); }
    .hmi-neutral { color: var(--c-neutral); }

    /* ── Tarjetas de variables HMI ───────────────────── */
    .hmi-var-card {
        border: 1.5px solid var(--c-border);
        border-radius: var(--radius-md);
        padding: 1rem 0.7rem 0.85rem;
        background: var(--c-surface);
        text-align: center;
        box-shadow: var(--shadow-sm);
        transition: box-shadow 0.15s;
    }
    .hmi-var-card:hover { box-shadow: var(--shadow-md); }
    .hmi-var-card.normal      { border-color: var(--c-ok-border);      background: var(--c-ok-bg); }
    .hmi-var-card.advertencia { border-color: var(--c-warn-border);    background: var(--c-warn-bg); }
    .hmi-var-card.critico     { border-color: var(--c-alert-border);   background: var(--c-alert-bg); }
    .hmi-var-card.sin-dato    { border-color: var(--c-neutral-border); background: var(--c-neutral-bg); }

    .hmi-var-icon {
        display: flex;
        justify-content: center;
        margin-bottom: 0.3rem;
    }
    .hmi-var-icon svg { opacity: 0.55; }
    .hmi-var-card.normal      .hmi-var-icon svg { color: var(--c-ok);      opacity: 0.8; }
    .hmi-var-card.advertencia .hmi-var-icon svg { color: var(--c-warn);    opacity: 0.8; }
    .hmi-var-card.critico     .hmi-var-icon svg { color: var(--c-alert);   opacity: 0.8; }

    .hmi-var-name {
        font-size: 0.63rem;
        font-weight: 800;
        color: var(--c-text-sub);
        text-transform: uppercase;
        letter-spacing: 0.07em;
        margin-top: 0.1rem;
    }
    .hmi-var-value {
        font-size: 1.65rem;
        font-weight: 800;
        color: var(--c-text-main);
        line-height: 1.1;
        margin: 0.3rem 0 0.2rem 0;
        font-variant-numeric: tabular-nums;
        letter-spacing: -0.02em;
    }
    .hmi-var-minmax { font-size: 0.67rem; color: var(--c-text-sub);   margin-bottom: 0.12rem; }
    .hmi-var-range  { font-size: 0.64rem; color: var(--c-text-muted); margin-bottom: 0.35rem; }

    .hmi-var-status {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        font-size: 0.72rem;
        font-weight: 700;
        padding: 0.15rem 0.55rem;
        border-radius: 999px;
    }
    .hmi-var-status.normal      { color: var(--c-ok);      background: var(--c-ok-pill); }
    .hmi-var-status.advertencia { color: var(--c-warn);    background: var(--c-warn-pill); }
    .hmi-var-status.critico     { color: var(--c-alert);   background: var(--c-alert-pill); }
    .hmi-var-status.sin-dato    { color: var(--c-text-sub); background: var(--c-neutral-pill); }

    /* ── Tablero de actuadores ───────────────────────── */
    .hmi-act-card {
        border: 1.5px solid var(--c-border);
        border-radius: var(--radius-md);
        padding: 0.75rem 0.45rem 0.65rem;
        text-align: center;
        background: var(--c-neutral-bg);
        width: 100%;
        box-sizing: border-box;
        box-shadow: var(--shadow-sm);
    }
    .hmi-act-card.cmd-on  {
        border-color: var(--c-ok-border);
        background: var(--c-ok-bg);
    }
    .hmi-act-card.cmd-off {
        border-color: var(--c-border-sub);
        background: var(--c-neutral-bg);
    }

    .hmi-pilot-wrap {
        display: flex;
        justify-content: center;
        margin-bottom: 0.35rem;
    }
    .hmi-pilot {
        width: 12px; height: 12px;
        border-radius: 50%;
        display: inline-block;
        flex-shrink: 0;
    }
    .hmi-pilot.on  {
        background: #22C55E;
        box-shadow: 0 0 0 3px #22C55E28, 0 0 8px #22C55E66;
    }
    .hmi-pilot.off { background: #CBD5E1; }

    .hmi-act-icon  {
        display: flex;
        justify-content: center;
        margin-bottom: 0.2rem;
    }
    .hmi-act-icon svg { opacity: 0.5; }
    .hmi-act-card.cmd-on .hmi-act-icon svg { opacity: 0.75; color: var(--c-ok); }

    .hmi-act-name {
        font-size: 0.68rem;
        font-weight: 700;
        color: var(--c-text-main);
        display: block;
        margin-bottom: 0.18rem;
        letter-spacing: 0.02em;
    }
    .hmi-act-cmd  {
        font-size: 0.63rem;
        color: var(--c-text-sub);
        display: block;
        margin-bottom: 0.06rem;
    }
    .hmi-act-desc { font-size: 0.60rem; color: var(--c-text-muted); display: block; }

    .hmi-act-note {
        font-size: 0.64rem;
        color: var(--c-text-muted);
        border-left: 3px solid var(--c-border);
        padding: 0.3rem 0 0.3rem 0.6rem;
        margin-top: 0.6rem;
        line-height: 1.55;
        background: var(--c-neutral-bg);
        border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
    }

    /* ── Tarjetas de alarma ──────────────────────────── */
    .alarm-card {
        border-left: 3px solid var(--c-border);
        border-radius: 0 var(--radius-md) var(--radius-md) 0;
        padding: 0.6rem 0.85rem;
        margin-bottom: 0.45rem;
        background: var(--c-neutral-bg);
        line-height: 1.55;
        box-shadow: var(--shadow-sm);
    }
    .alarm-card.warn     { border-left-color: #F59E0B; background: var(--c-warn-bg); }
    .alarm-card.critical { border-left-color: #EF4444; background: var(--c-alert-bg); }

    .alarm-header {
        display: flex;
        align-items: center;
        gap: 0.35rem;
        font-size: 0.74rem;
        font-weight: 800;
        margin-bottom: 0.22rem;
    }
    .alarm-header.warn     { color: #92400E; }
    .alarm-header.critical { color: #991B1B; }

    .alarm-detail { font-size: 0.71rem; color: var(--c-text-main); }
    .alarm-action {
        font-size: 0.70rem;
        color: var(--c-accent);
        margin-top: 0.22rem;
        border-top: 1px dashed var(--c-border-sub);
        padding-top: 0.22rem;
        display: flex;
        align-items: flex-start;
        gap: 0.3rem;
    }

    /* ── Misc ───────────────────────────────────────── */
    .subtle {
        color: var(--c-text-muted);
        font-size: 0.80rem;
        display: flex;
        align-items: center;
        gap: 0.35rem;
    }

    /* ── KPI section heading ────────────────────────── */
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
    .hmi-section-heading svg { opacity: 0.6; }

    /* ── Métricas nativas de Streamlit ──────────────── */
    [data-testid="stMetric"] {
        background: var(--c-neutral-bg);
        border: 1px solid var(--c-border);
        border-radius: var(--radius-md);
        padding: 0.65rem 0.85rem 0.55rem;
    }
    [data-testid="stMetricLabel"] { font-size: 0.68rem !important; color: var(--c-text-sub) !important; font-weight: 700 !important; text-transform: uppercase; letter-spacing: 0.06em; }
    [data-testid="stMetricValue"] { font-size: 1.55rem !important; color: var(--c-text-main) !important; font-weight: 800 !important; }

    /* ── Tarjetas de ambiente ──────────────────────── */
    .ambiente-card-header {
        display: flex;
        align-items: baseline;
        gap: 0.5rem;
        margin-bottom: 0.15rem;
    }
    .ambiente-card-header h4 {
        font-size: 1rem;
        font-weight: 800;
        color: var(--c-text-main);
        margin: 0;
    }
    /* ── Expander ────────────────────────────────────── */
    [data-testid="stExpander"] {
        border: 1px solid var(--c-border) !important;
        border-radius: var(--radius-md) !important;
        background: var(--c-neutral-bg) !important;
    }

    /* ── Divisor ─────────────────────────────────────── */
    hr[data-testid="stDivider"] {
        border-color: var(--c-border) !important;
        margin: 0.6rem 0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# Configuración
# =========================================================
RANGOS = {
    "temperatura": (18, 22),
    "humedad": (85, 95),
    "co2": (None, 1000),
}

# Límites de plausibilidad física — valores fuera de estos rangos
# son imposibles y se descartan como ruido del sensor.
LIMITES_FISICOS = {
    "temperatura": (-10.0, 60.0),   # °C
    "humedad": (0.0, 100.0),         # %RH: no puede superar 100 %
    "co2": (0.0, 10000.0),           # ppm: rango razonable para interiores
}

# Márgenes para nivel de advertencia (fuera del rango operativo pero dentro del margen)
WARN_MARGEN = {
    "temperatura": 3,    # advertencia: ±3 °C alrededor del rango operativo
    "humedad": 5,         # advertencia: ±5 %RH
    "co2": 200,           # advertencia: hasta 200 ppm por encima del límite
}

UNIDADES = {
    "temperatura": "°C",
    "humedad": "%",
    "co2": "ppm",
}

DECIMALES = {
    "temperatura": 1,
    "humedad": 1,
    "co2": 0,
}

TIMESTAMP_KEYS = [
    "timestamp",
    "updated_at",
    "fecha_hora",
    "fecha",
    "last_update",
    "ultima_actualizacion",
]

STALE_MINUTES = 5

# Acciones sugeridas para el operario según variable y condición
ACCIONES_SUGERIDAS = {
    ("temperatura", "bajo"): (
        "Verificar cierre de puertas, ventilación no deseada y estado del calefactor."
    ),
    ("temperatura", "alto"): (
        "Verificar ventilación, extracción y carga térmica del ambiente."
    ),
    ("humedad", "bajo"): (
        "Verificar nivel de agua, nebulizador, electroválvula y fugas de aire."
    ),
    ("humedad", "alto"): (
        "Reducir nebulización y verificar renovación de aire."
    ),
    ("co2", "alto"): (
        "Verificar extracción o renovación de aire."
    ),
    ("comunicacion", "sin_dato"): (
        "Revisar alimentación de sensores, conexión con Raspberry Pi y comunicación con API."
    ),
}

# Configuración del tablero de actuadores
ACTUADORES_CONFIG = [
    {
        "key": "calefactor",
        "nombre": "Calefactor",
        "svg_key": "calefactor",
        "desc_on": "Salida activada",
        "desc_off": "Salida desactivada",
    },
    {
        "key": "extractor",
        "nombre": "Extractor",
        "svg_key": "extractor",
        "desc_on": "Salida activada",
        "desc_off": "Salida desactivada",
    },
    {
        "key": "nebulizador",
        "nombre": "Nebulizador",
        "svg_key": "nebulizador",
        "desc_on": "Salida activada",
        "desc_off": "Salida desactivada",
    },
]


# =========================================================
# Utilidades generales
# =========================================================
def formatear_valor(valor, variable):
    if valor is None or pd.isna(valor):
        return "N/D"
    dec = DECIMALES.get(variable, 2)
    unidad = UNIDADES.get(variable, "")
    return f"{valor:.{dec}f} {unidad}".strip()


def formatear_rango(vmin, vmax, variable):
    if vmin is None or vmax is None or pd.isna(vmin) or pd.isna(vmax):
        return "N/D"
    dec = DECIMALES.get(variable, 2)
    unidad = UNIDADES.get(variable, "")
    return f"{vmin:.{dec}f}–{vmax:.{dec}f} {unidad}".strip()


def extraer_timestamp(registro):
    for key in TIMESTAMP_KEYS:
        if key in registro and registro.get(key):
            ts = pd.to_datetime(registro.get(key), errors="coerce")
            if pd.notna(ts):
                return ts
    return pd.NaT


def tiempo_relativo(ts):
    if pd.isna(ts):
        return "Sin timestamp"

    now = pd.Timestamp.now(tz=ts.tz) if getattr(ts, "tzinfo", None) else pd.Timestamp.now()
    delta = now - ts

    if delta.total_seconds() < 0:
        return "Ahora"

    segundos = int(delta.total_seconds())
    if segundos < 60:
        return f"Hace {segundos}s"
    minutos = segundos // 60
    if minutos < 60:
        return f"Hace {minutos} min"
    horas = minutos // 60
    if horas < 24:
        return f"Hace {horas} h"
    dias = horas // 24
    return f"Hace {dias} d"


def en_rango(variable, valor):
    if valor is None or pd.isna(valor):
        return None
    minimo, maximo = RANGOS.get(variable, (None, None))
    if minimo is not None and valor < minimo:
        return False
    if maximo is not None and valor > maximo:
        return False
    return True


def evaluar_serie(variable, serie):
    serie = pd.to_numeric(serie, errors="coerce").dropna()
    if serie.empty:
        return "Sin dato", "neutral"
    estados = [en_rango(variable, v) for v in serie]
    if all(e is True for e in estados):
        return "En rango", "ok"
    minimo, maximo = RANGOS.get(variable, (None, None))
    hay_bajos = minimo is not None and (serie < minimo).any()
    hay_altos = maximo is not None and (serie > maximo).any()
    if hay_bajos and hay_altos:
        return "Dispersión / fuera de rango", "alert"
    if hay_bajos:
        return "Baja en ≥1 sensor", "alert"
    if hay_altos:
        return "Alta en ≥1 sensor", "alert"
    return "Fuera de rango", "alert"


def evaluar_severidad(variable, valor):
    """
    Evalúa la severidad de un valor individual respecto al rango operativo y
    los márgenes de advertencia configurados.

    Returns: 'normal' | 'advertencia' | 'critico' | None (sin dato)
    """
    if valor is None or pd.isna(valor):
        return None

    vmin, vmax = RANGOS.get(variable, (None, None))
    margen = WARN_MARGEN.get(variable, 0)

    # Dentro del rango operativo
    if (vmin is None or valor >= vmin) and (vmax is None or valor <= vmax):
        return "normal"

    # Fuera del rango operativo — ¿dentro del margen de advertencia?
    warn_min = (vmin - margen) if vmin is not None else None
    warn_max = (vmax + margen) if vmax is not None else None

    if (warn_min is None or valor >= warn_min) and (warn_max is None or valor <= warn_max):
        return "advertencia"

    return "critico"


def badge_html(texto, tipo):
    clases = {
        "ok":      "badge badge-ok",
        "warn":    "badge badge-warn",
        "alert":   "badge badge-alert",
        "neutral": "badge badge-neutral",
    }
    svg_map = {
        "ok":      SVG_ICONS["check"],
        "warn":    SVG_ICONS["warn"],
        "alert":   SVG_ICONS["critical"],
        "neutral": "",
    }
    return (
        f'<span class="{clases.get(tipo, "badge badge-neutral")}">'
        f'{svg_map.get(tipo, "")}{texto}'
        f'</span>'
    )


def limpiar_valor_fisico(variable, valor):
    """
    Descarta valores físicamente imposibles devolviendo NaN.
    Esto filtra lecturas con ruido extremo (p. ej., humedad de 3313 %).
    """
    if pd.isna(valor):
        return float("nan")
    lmin, lmax = LIMITES_FISICOS.get(variable, (None, None))
    if lmin is not None and valor < lmin:
        return float("nan")
    if lmax is not None and valor > lmax:
        return float("nan")
    return valor


# =========================================================
# Procesamiento de sensores
# =========================================================
def normalizar_sensores(sensores):
    filas = []
    for i, sensor in enumerate(sensores, start=1):
        filas.append(
            {
                "sensor_id": sensor.get("sensor_id", f"S{i}"),
                "temperatura": sensor.get("temperatura"),
                "humedad": sensor.get("humedad"),
                "co2": sensor.get("co2"),
                "estado_sensor": str(sensor.get("estado_sensor", "DESCONOCIDO")).upper(),
                "timestamp": extraer_timestamp(sensor),
            }
        )

    df = pd.DataFrame(filas).reindex(
        columns=["sensor_id", "temperatura", "humedad", "co2", "estado_sensor", "timestamp"]
    )

    for col in ["temperatura", "humedad", "co2"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        # Filtrar valores físicamente imposibles (ruido de sensor)
        df[col] = df[col].apply(lambda v: limpiar_valor_fisico(col, v))

    return df


def resumir_variable(df, variable):
    serie = df[variable].dropna()

    if serie.empty:
        return {
            "avg": None,
            "min": None,
            "max": None,
            "label": "Sin dato",
            "severity": "neutral",
        }

    label, severity = evaluar_serie(variable, serie)

    return {
        "avg": float(serie.mean()),
        "min": float(serie.min()),
        "max": float(serie.max()),
        "label": label,
        "severity": severity,
    }


def clasificar_ambiente(df_sensores):
    if df_sensores.empty:
        return {
            "status_text": "Sin telemetría",
            "status_type": "neutral",
            "alerts": ["No hay telemetría disponible para este ambiente."],
            "last_ts": pd.NaT,
            "stale": False,
        }

    alerts = []

    last_ts = (
        df_sensores["timestamp"].dropna().max()
        if df_sensores["timestamp"].notna().any()
        else pd.NaT
    )
    stale = False

    if pd.notna(last_ts):
        now = (
            pd.Timestamp.now(tz=last_ts.tz)
            if getattr(last_ts, "tzinfo", None)
            else pd.Timestamp.now()
        )
        stale = (now - last_ts) > pd.Timedelta(minutes=STALE_MINUTES)
        if stale:
            alerts.append("Telemetría atrasada.")
    else:
        alerts.append("No se recibió timestamp de actualización.")

    if (df_sensores["estado_sensor"] != "OK").any():
        alerts.append("Uno o más sensores reportan estado no OK.")

    for variable, nombre in [
        ("temperatura", "Temperatura"),
        ("humedad", "Humedad"),
        ("co2", "CO₂"),
    ]:
        label, severity = evaluar_serie(variable, df_sensores[variable])
        if severity == "alert":
            alerts.append(f"{nombre} fuera de rango en al menos un sensor.")

    hay_faltantes = df_sensores[["temperatura", "humedad", "co2"]].isna().any().any()

    if any("fuera de rango" in a.lower() for a in alerts) or any(
        "no ok" in a.lower() for a in alerts
    ):
        return {
            "status_text": "Atención requerida",
            "status_type": "alert",
            "alerts": alerts,
            "last_ts": last_ts,
            "stale": stale,
        }

    if stale or hay_faltantes:
        return {
            "status_text": "Datos parciales",
            "status_type": "warn",
            "alerts": alerts,
            "last_ts": last_ts,
            "stale": stale,
        }

    return {
        "status_text": "Operación normal",
        "status_type": "ok",
        "alerts": alerts,
        "last_ts": last_ts,
        "stale": stale,
    }


# =========================================================
# Generación de alarmas detalladas
# =========================================================
def generar_alarmas_detalle(df_sensores, clasificacion):
    """
    Genera una lista de dicts con información detallada de cada alarma
    detectada, incluyendo sensor afectado, valor, rango y acción sugerida.
    """
    alarmas = []
    stale = clasificacion["stale"]

    # Alarma de comunicación
    if df_sensores.empty:
        alarmas.append(
            {
                "nivel": "advertencia",
                "variable": "Comunicación con sensores",
                "sensor_id": None,
                "valor_str": None,
                "rango_str": None,
                "condicion": "Sin telemetría",
                "accion": ACCIONES_SUGERIDAS[("comunicacion", "sin_dato")],
            }
        )
        return alarmas

    if stale:
        alarmas.append(
            {
                "nivel": "advertencia",
                "variable": "Comunicación con sensores",
                "sensor_id": None,
                "valor_str": None,
                "rango_str": None,
                "condicion": "Telemetría atrasada",
                "accion": ACCIONES_SUGERIDAS[("comunicacion", "sin_dato")],
            }
        )

    # Alarmas por variable y sensor
    for variable, nombre_var in [
        ("temperatura", "Temperatura"),
        ("humedad", "Humedad relativa"),
        ("co2", "CO₂"),
    ]:
        vmin, vmax = RANGOS.get(variable, (None, None))
        unidad = UNIDADES.get(variable, "")

        if vmin is not None and vmax is not None:
            rango_str = f"{vmin}–{vmax} {unidad}"
        elif vmax is not None:
            rango_str = f"< {vmax} {unidad}"
        else:
            rango_str = "N/D"

        for _, row in df_sensores.iterrows():
            val = row[variable]
            sensor_id = row["sensor_id"]

            if pd.isna(val):
                alarmas.append(
                    {
                        "nivel": "advertencia",
                        "variable": nombre_var,
                        "sensor_id": sensor_id,
                        "valor_str": None,
                        "rango_str": rango_str,
                        "condicion": "Sin dato",
                        "accion": ACCIONES_SUGERIDAS[("comunicacion", "sin_dato")],
                    }
                )
                continue

            sev = evaluar_severidad(variable, val)
            if sev in ("advertencia", "critico"):
                if vmax is not None and val > vmax:
                    condicion = "Alto"
                    accion_key = (variable, "alto")
                elif vmin is not None and val < vmin:
                    condicion = "Bajo"
                    accion_key = (variable, "bajo")
                else:
                    condicion = "Fuera de rango"
                    accion_key = (variable, "alto")

                alarmas.append(
                    {
                        "nivel": sev,
                        "variable": nombre_var,
                        "sensor_id": sensor_id,
                        "valor_str": formatear_valor(val, variable),
                        "rango_str": rango_str,
                        "condicion": condicion,
                        "accion": ACCIONES_SUGERIDAS.get(
                            accion_key, "Revisar el sistema."
                        ),
                    }
                )

    return alarmas


# =========================================================
# Componentes de visualización HMI
# =========================================================
def render_estado_sistema(clasificacion, df_sensores):
    """Panel de estado operativo tipo HMI — barra superior por ambiente."""
    status_text = clasificacion["status_text"]
    status_type = clasificacion["status_type"]
    last_ts = clasificacion["last_ts"]
    stale = clasificacion["stale"]
    alerts = [a for a in clasificacion["alerts"] if a]

    # Estado de comunicación
    if df_sensores.empty:
        com_txt, com_cls = "Sin datos", "hmi-alert"
    elif stale:
        com_txt, com_cls = "Atrasada", "hmi-warn"
    else:
        com_txt, com_cls = "OK", "hmi-ok"

    # Estado de alarmas
    n_alarmas = len(alerts)
    alarm_txt = "Sin alarmas" if n_alarmas == 0 else f"{n_alarmas} activa(s)"
    alarm_cls = "hmi-ok" if n_alarmas == 0 else "hmi-alert"

    # Estado general
    status_cls_map = {
        "ok":      "hmi-ok",
        "warn":    "hmi-warn",
        "alert":   "hmi-alert",
        "neutral": "hmi-neutral",
    }
    status_cls = status_cls_map.get(status_type, "hmi-neutral")

    ts_txt = (
        last_ts.strftime("%H:%M:%S") if pd.notna(last_ts) else "N/D"
    )
    ts_fecha = (
        last_ts.strftime("%Y-%m-%d") if pd.notna(last_ts) else ""
    )
    sensores_count = len(df_sensores)

    dot_ok   = f'<span style="color:var(--c-ok)">{SVG_ICONS["estado"]}</span>'
    dot_warn = f'<span style="color:var(--c-warn)">{SVG_ICONS["estado"]}</span>'
    dot_alert= f'<span style="color:var(--c-alert)">{SVG_ICONS["estado"]}</span>'
    dot_neu  = f'<span style="color:var(--c-neutral)">{SVG_ICONS["estado"]}</span>'

    dot_status = {"hmi-ok": dot_ok, "hmi-warn": dot_warn, "hmi-alert": dot_alert, "hmi-neutral": dot_neu}

    html = f"""
    <p class="section-title">{SVG_ICONS['gear']} Estado del sistema</p>
    <div class="hmi-status-bar">
        <div class="hmi-status-cell">
            <div class="hmi-status-label">Estado general</div>
            <div class="hmi-status-value {status_cls}">{dot_status.get(status_cls, dot_neu)} {status_text}</div>
        </div>
        <div class="hmi-status-cell">
            <div class="hmi-status-label">Modo de control</div>
            <div class="hmi-status-value hmi-ok">{dot_ok} Automático</div>
        </div>
        <div class="hmi-status-cell">
            <div class="hmi-status-label">Comunicación</div>
            <div class="hmi-status-value {com_cls}">{dot_status.get(com_cls, dot_neu)} {com_txt}</div>
        </div>
        <div class="hmi-status-cell">
            <div class="hmi-status-label">{SVG_ICONS['clock']} Última telemetría</div>
            <div class="hmi-status-value hmi-neutral">{ts_txt}</div>
            <div class="hmi-status-label">{ts_fecha}</div>
        </div>
        <div class="hmi-status-cell">
            <div class="hmi-status-label">Sensores reportando</div>
            <div class="hmi-status-value hmi-neutral">{sensores_count}</div>
        </div>
        <div class="hmi-status-cell">
            <div class="hmi-status-label">{SVG_ICONS['alarm']} Alarmas</div>
            <div class="hmi-status-value {alarm_cls}">{dot_status.get(alarm_cls, dot_neu)} {alarm_txt}</div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def _html_tarjeta_variable(variable, svg_key, nombre_display, res):
    """Genera el HTML de una tarjeta HMI para una variable de proceso."""
    icono_svg = SVG_ICONS.get(svg_key, "")

    if res is None or res["avg"] is None:
        return f"""
        <div class="hmi-var-card sin-dato">
            <div class="hmi-var-icon">{icono_svg}</div>
            <div class="hmi-var-name">{nombre_display}</div>
            <div class="hmi-var-value">N/D</div>
            <div class="hmi-var-minmax">—</div>
            <div class="hmi-var-range">—</div>
            <div class="hmi-var-status sin-dato">Sin dato</div>
        </div>
        """

    avg = res["avg"]
    sev = evaluar_severidad(variable, avg) or "sin-dato"
    val_str = formatear_valor(avg, variable)

    min_str = formatear_valor(res["min"], variable)
    max_str = formatear_valor(res["max"], variable)
    minmax_str = f"Mín {min_str} · Máx {max_str}" if res["min"] is not None else "—"

    vmin_r, vmax_r = RANGOS.get(variable, (None, None))
    if vmin_r is not None and vmax_r is not None:
        rango_str = f"Objetivo: {formatear_rango(vmin_r, vmax_r, variable)}"
    elif vmax_r is not None:
        rango_str = f"Objetivo: &lt; {formatear_valor(vmax_r, variable)}"
    else:
        rango_str = "Sin rango definido"

    status_icons_svg = {
        "normal":      SVG_ICONS["check"]    + " En rango",
        "advertencia": SVG_ICONS["warn"]     + " Advertencia",
        "critico":     SVG_ICONS["critical"] + " Crítico",
        "sin-dato":    "Sin dato",
    }
    status_label = status_icons_svg.get(sev, "Sin dato")

    return f"""
    <div class="hmi-var-card {sev}">
        <div class="hmi-var-icon">{icono_svg}</div>
        <div class="hmi-var-name">{nombre_display}</div>
        <div class="hmi-var-value">{val_str}</div>
        <div class="hmi-var-minmax">{minmax_str}</div>
        <div class="hmi-var-range">{rango_str}</div>
        <div class="hmi-var-status {sev}">{status_label}</div>
    </div>
    """


def render_tarjetas_hmi(resumen):
    """Renderiza las tres tarjetas de variables críticas de proceso."""
    st.markdown(
        f'<p class="section-title">{SVG_ICONS["overview"]} Variables críticas de proceso</p>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            _html_tarjeta_variable("temperatura", "temperatura", "Temperatura", resumen["temperatura"]),
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            _html_tarjeta_variable("humedad", "humedad", "Humedad relativa", resumen["humedad"]),
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            _html_tarjeta_variable("co2", "co2", "CO₂", resumen["co2"]),
            unsafe_allow_html=True,
        )


def _html_piloto(nombre, svg_key, pilot_cls, card_cls, cmd_txt, desc_txt):
    """Genera el HTML de una tarjeta piloto individual para el tablero de actuadores."""
    icono_svg = SVG_ICONS.get(svg_key, "")
    return f"""
    <div class="hmi-act-card {card_cls}">
        <div class="hmi-pilot-wrap">
            <span class="hmi-pilot {pilot_cls}"></span>
        </div>
        <div class="hmi-act-icon">{icono_svg}</div>
        <span class="hmi-act-name">{nombre}</span>
        <span class="hmi-act-cmd">{cmd_txt}</span>
        <span class="hmi-act-desc">{desc_txt}</span>
    </div>
    """


def render_tablero_actuadores(actuadores, clasificacion, df_sensores):
    """
    Tablero de señalización de salidas tipo piloto industrial.
    Muestra el estado lógico de cada salida enviada al relé.
    Usa st.columns() para garantizar el layout correcto en Streamlit.
    """
    st.markdown(
        f'<p class="section-title">{SVG_ICONS["plug"]} Tablero de señalización de salidas</p>',
        unsafe_allow_html=True,
    )

    stale = clasificacion["stale"]
    com_ok = not df_sensores.empty and not stale

    # Construir lista de indicadores: 3 actuadores + control auto + sensores
    indicadores = []

    for cfg in ACTUADORES_CONFIG:
        activo = bool(actuadores.get(cfg["key"], False))
        indicadores.append(
            {
                "nombre": cfg["nombre"],
                "svg_key": cfg["svg_key"],
                "pilot": "on" if activo else "off",
                "card": "cmd-on" if activo else "cmd-off",
                "cmd": "Comando ON" if activo else "Comando OFF",
                "desc": cfg["desc_on"] if activo else cfg["desc_off"],
            }
        )

    indicadores.append(
        {
            "nombre": "Control auto.",
            "svg_key": "control",
            "pilot": "on",
            "card": "cmd-on",
            "cmd": "Activo",
            "desc": "Modo automático",
        }
    )

    indicadores.append(
        {
            "nombre": "Sensores",
            "svg_key": "sensor",
            "pilot": "on" if com_ok else "off",
            "card": "cmd-on" if com_ok else "cmd-off",
            "cmd": "Comunicación OK" if com_ok else "Atrasada",
            "desc": "Datos recientes" if com_ok else "Verificar sensores",
        }
    )

    # Renderizar con st.columns() — garantiza distribución correcta en Streamlit
    cols = st.columns(len(indicadores))
    for col, ind in zip(cols, indicadores):
        with col:
            st.markdown(
                _html_piloto(
                    ind["nombre"],
                    ind["svg_key"],
                    ind["pilot"],
                    ind["card"],
                    ind["cmd"],
                    ind["desc"],
                ),
                unsafe_allow_html=True,
            )

    # Nota técnica debajo del tablero
    st.markdown(
        f"""
        <div class="hmi-act-note">
            {SVG_ICONS['info']} El estado mostrado corresponde a la salida lógica enviada al relé.
            La confirmación física del actuador requiere sensor de corriente,
            contacto auxiliar o señal de retorno.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_alarmas(alarmas):
    """Renderiza cada alarma como una tarjeta individual con detalle operativo."""
    if not alarmas:
        st.success("Sin alarmas activas. Ambiente en rango y sensores operando correctamente.")
        return

    st.markdown(
        f'<p class="section-title">{SVG_ICONS["alarm"]} Alarmas activas</p>',
        unsafe_allow_html=True,
    )

    for alarma in alarmas:
        nivel = alarma["nivel"]
        card_type = "critical" if nivel == "critico" else "warn"
        nivel_icon = SVG_ICONS["critical"] + " CRÍTICO" if nivel == "critico" else SVG_ICONS["warn"] + " ADVERTENCIA"

        partes_detalle = []
        if alarma["sensor_id"] is not None:
            partes_detalle.append(f"Sensor: <b>{alarma['sensor_id']}</b>")
        if alarma["valor_str"]:
            partes_detalle.append(f"Valor medido: <b>{alarma['valor_str']}</b>")
        if alarma["rango_str"]:
            partes_detalle.append(f"Rango recomendado: <b>{alarma['rango_str']}</b>")
        if alarma["condicion"]:
            partes_detalle.append(f"Condición: <b>{alarma['condicion']}</b>")

        detalle_html = " &nbsp;|&nbsp; ".join(partes_detalle)

        html = f"""
        <div class="alarm-card {card_type}">
            <div class="alarm-header {card_type}">{nivel_icon} &nbsp;{alarma['variable']}</div>
            <div class="alarm-detail">{detalle_html}</div>
            <div class="alarm-action">{SVG_ICONS['info']} {alarma['accion']}</div>
        </div>
        """
        st.markdown(html, unsafe_allow_html=True)


# =========================================================
# Lógica principal
# =========================================================
try:
    ambientes = get_ambientes() or []
    estados = get_estados_ambientes() or []

    if not ambientes:
        st.warning("No hay ambientes registrados en el sistema.")
        st.stop()

    estados_map = {
        str(e.get("ambiente_id")): e
        for e in estados
        if e.get("ambiente_id") is not None
    }

    ambientes_procesados = []

    for ambiente in ambientes:
        ambiente_id = str(ambiente.get("ambiente_id"))
        nombre = ambiente.get("nombre", f"Ambiente {ambiente_id}")

        estado_raw = estados_map.get(ambiente_id, {})
        sensores_raw = estado_raw.get("sensores", []) or []
        actuadores = estado_raw.get("actuadores", {}) or {}

        df_sensores = normalizar_sensores(sensores_raw)

        resumen = {
            "temperatura": resumir_variable(df_sensores, "temperatura") if not df_sensores.empty else None,
            "humedad": resumir_variable(df_sensores, "humedad") if not df_sensores.empty else None,
            "co2": resumir_variable(df_sensores, "co2") if not df_sensores.empty else None,
        }

        clasificacion = clasificar_ambiente(df_sensores)
        alarmas = generar_alarmas_detalle(df_sensores, clasificacion)

        ambientes_procesados.append(
            {
                "ambiente_id": ambiente_id,
                "nombre": nombre,
                "df_sensores": df_sensores,
                "actuadores": actuadores,
                "resumen": resumen,
                "clasificacion": clasificacion,
                "alarmas": alarmas,
            }
        )

    # -------------------------
    # Barra de filtro y hora
    # -------------------------
  # -------------------------
# Barra de filtro y hora
# -------------------------
    f1, f2, f3 = st.columns([1, 2, 1])

    with f1:
        solo_alertas = st.checkbox("Solo alertas", value=False)

    with f2:
        st.markdown(
            f"""
            <div style="
                display:flex;
                justify-content:center;
                align-items:center;
                width:100%;
                color:#17211A;
                font-size:0.80rem;
            ">
                {SVG_ICONS["clock"]}&nbsp; Actualizado: {pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")}
            </div>
            """,
            unsafe_allow_html=True,
        )

    with f3:
        st.write("")
    # -------------------------
    # KPIs globales
    # -------------------------
    total_ambientes = len(ambientes_procesados)
    ambientes_con_telemetria = sum(
        1 for a in ambientes_procesados if not a["df_sensores"].empty
    )
    ambientes_alerta = sum(
        1 for a in ambientes_procesados if a["clasificacion"]["status_type"] == "alert"
    )
    ambientes_parciales = sum(
        1 for a in ambientes_procesados if a["clasificacion"]["status_type"] == "warn"
    )
    sensores_reportando = sum(len(a["df_sensores"]) for a in ambientes_procesados)

    with st.container(border=True):
        st.markdown(
            f'<div class="hmi-section-heading">{SVG_ICONS["overview"]} Visión general del sistema</div>',
            unsafe_allow_html=True,
        )
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Ambientes", total_ambientes)
        k2.metric("Con telemetría", ambientes_con_telemetria)
        k3.metric("En alerta", ambientes_alerta)
        k4.metric("Datos parciales", ambientes_parciales)
        k5.metric("Sensores reportando", sensores_reportando)
        st.write("")

    st.write("")

    # -------------------------
    # Tarjetas por ambiente
    # -------------------------
    visibles = [
        a for a in ambientes_procesados
        if (not solo_alertas) or a["clasificacion"]["status_type"] == "alert"
    ]

    if not visibles:
        st.info("No hay ambientes en alerta con el filtro actual.")
        st.stop()

    cols = st.columns(min(2, len(visibles)))

    for i, ambiente in enumerate(visibles):
        col = cols[i % 2]

        with col:
            nombre = ambiente["nombre"]
            ambiente_id = ambiente["ambiente_id"]
            df_sensores = ambiente["df_sensores"]
            actuadores = ambiente["actuadores"]
            resumen = ambiente["resumen"]
            clasificacion = ambiente["clasificacion"]
            alarmas = ambiente["alarmas"]

            with st.container(border=True):
                # Encabezado del ambiente
                st.markdown(
                    f'<div class="ambiente-card-header">'
                    f'<h4>{nombre}</h4>'
                    f'{badge_html(clasificacion["status_text"], clasificacion["status_type"])}'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div class="subtle" style="margin-bottom:0.5rem">ID: <b>{ambiente_id}</b></div>',
                    unsafe_allow_html=True,
                )

                st.divider()

                # ── 1. Panel de estado del sistema ──────────────
                render_estado_sistema(clasificacion, df_sensores)

                if df_sensores.empty:
                    st.info("Sin telemetría actual.")
                    continue

                st.write("")

                # ── 2. Tarjetas de variables críticas HMI ───────
                render_tarjetas_hmi(resumen)

                st.write("")

                # ── 3. Tablero de señalización de salidas ────────
                render_tablero_actuadores(actuadores, clasificacion, df_sensores)

                st.write("")

                # ── 4. Alarmas detalladas ────────────────────────
                render_alarmas(alarmas)

                # ── Detalle por sensor (expander) ────────────────
                with st.expander("Ver detalle por sensor"):
                    detalle = df_sensores.copy()

                    detalle["temp_estado"] = detalle["temperatura"].apply(
                        lambda x: evaluar_serie("temperatura", pd.Series([x]))[0]
                        if pd.notna(x)
                        else "Sin dato"
                    )
                    detalle["hum_estado"] = detalle["humedad"].apply(
                        lambda x: evaluar_serie("humedad", pd.Series([x]))[0]
                        if pd.notna(x)
                        else "Sin dato"
                    )
                    detalle["co2_estado"] = detalle["co2"].apply(
                        lambda x: evaluar_serie("co2", pd.Series([x]))[0]
                        if pd.notna(x)
                        else "Sin dato"
                    )

                    detalle["timestamp"] = detalle["timestamp"].apply(
                        lambda x: x.strftime("%Y-%m-%d %H:%M:%S") if pd.notna(x) else "N/D"
                    )

                    detalle = detalle.rename(
                        columns={
                            "sensor_id": "sensor_id",
                            "temperatura": "temperatura (°C)",
                            "humedad": "humedad (%)",
                            "co2": "co2 (ppm)",
                            "estado_sensor": "estado_sensor",
                            "timestamp": "timestamp",
                            "temp_estado": "estado_temp",
                            "hum_estado": "estado_humedad",
                            "co2_estado": "estado_co2",
                        }
                    )

                    st.caption(
                        "Los valores físicamente imposibles (p. ej., humedad > 100 %) "
                        "son descartados automáticamente y aparecen como N/D."
                    )

                    st.dataframe(
                        detalle.reindex(
                            columns=[
                                "sensor_id",
                                "temperatura (°C)",
                                "estado_temp",
                                "humedad (%)",
                                "estado_humedad",
                                "co2 (ppm)",
                                "estado_co2",
                                "estado_sensor",
                                "timestamp",
                            ]
                        ),
                        use_container_width=True,
                        hide_index=True,
                    )

except Exception as e:
    st.error(f"Error crítico al cargar el dashboard: {e}")