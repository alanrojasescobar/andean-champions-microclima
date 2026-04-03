import streamlit as st
import pandas as pd

from api.client import get_ambientes, get_estados_ambientes
from components.header import render_header

st.set_page_config(page_title="Dashboard", layout="wide")
render_header("Dashboard General del Sistema")

# =========================================================
# Estilo visual mínimo y limpio
# =========================================================
st.markdown(
    """
    <style>
    .badge {
        display: inline-block;
        padding: 0.28rem 0.65rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 700;
        margin-left: 0.35rem;
        border: 1px solid transparent;
    }
    .badge-ok {
        background: #E8F5E9;
        color: #1B5E20;
        border-color: #A5D6A7;
    }
    .badge-warn {
        background: #FFF8E1;
        color: #8D6E00;
        border-color: #FFE082;
    }
    .badge-alert {
        background: #FFEBEE;
        color: #B71C1C;
        border-color: #EF9A9A;
    }
    .badge-neutral {
        background: #ECEFF1;
        color: #37474F;
        border-color: #CFD8DC;
    }
    .pill {
        display: inline-block;
        padding: 0.22rem 0.60rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 600;
        margin-right: 0.35rem;
        margin-bottom: 0.25rem;
        border: 1px solid transparent;
    }
    .pill-on {
        background: #E8F5E9;
        color: #1B5E20;
        border-color: #A5D6A7;
    }
    .pill-off {
        background: #F5F5F5;
        color: #616161;
        border-color: #E0E0E0;
    }
    .subtle {
        color: #6B7280;
        font-size: 0.86rem;
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


# =========================================================
# Utilidades
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


def badge_html(texto, tipo):
    clases = {
        "ok": "badge badge-ok",
        "warn": "badge badge-warn",
        "alert": "badge badge-alert",
        "neutral": "badge badge-neutral",
    }
    return f'<span class="{clases.get(tipo, "badge badge-neutral")}">{texto}</span>'


def actuator_pill(nombre, activo, icono):
    clase = "pill pill-on" if activo else "pill pill-off"
    estado = "ON" if activo else "OFF"
    return f'<span class="{clase}">{icono} {nombre}: {estado}</span>'


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

    last_ts = df_sensores["timestamp"].dropna().max() if df_sensores["timestamp"].notna().any() else pd.NaT
    stale = False

    if pd.notna(last_ts):
        now = pd.Timestamp.now(tz=last_ts.tz) if getattr(last_ts, "tzinfo", None) else pd.Timestamp.now()
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

    if any("fuera de rango" in a.lower() for a in alerts) or any("no ok" in a.lower() for a in alerts):
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

        ambientes_procesados.append(
            {
                "ambiente_id": ambiente_id,
                "nombre": nombre,
                "df_sensores": df_sensores,
                "actuadores": actuadores,
                "resumen": resumen,
                "clasificacion": clasificacion,
            }
        )

    # -------------------------
    # Barra superior de control
    # -------------------------
    f1, f2 = st.columns([1, 4])
    with f1:
        solo_alertas = st.checkbox("Solo alertas", value=False)
    with f2:
        st.markdown(
            f'<div class="subtle">Actualizado: {pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")}</div>',
            unsafe_allow_html=True,
        )

    # -------------------------
    # KPIs globales
    # -------------------------
    total_ambientes = len(ambientes_procesados)
    ambientes_con_telemetria = sum(1 for a in ambientes_procesados if not a["df_sensores"].empty)
    ambientes_alerta = sum(1 for a in ambientes_procesados if a["clasificacion"]["status_type"] == "alert")
    ambientes_parciales = sum(1 for a in ambientes_procesados if a["clasificacion"]["status_type"] == "warn")
    sensores_reportando = sum(len(a["df_sensores"]) for a in ambientes_procesados)

    with st.container(border=True):
        st.markdown("### 📊 Visión general del sistema")
        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Ambientes", total_ambientes)
        k2.metric("Con telemetría", ambientes_con_telemetria)
        k3.metric("En alerta", ambientes_alerta)
        k4.metric("Datos parciales", ambientes_parciales)
        k5.metric("Sensores reportando", sensores_reportando)

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

    cols = st.columns(2)

    for i, ambiente in enumerate(visibles):
        col = cols[i % 2]

        with col:
            nombre = ambiente["nombre"]
            ambiente_id = ambiente["ambiente_id"]
            df_sensores = ambiente["df_sensores"]
            actuadores = ambiente["actuadores"]
            resumen = ambiente["resumen"]
            clasificacion = ambiente["clasificacion"]

            with st.container(border=True):
                st.markdown(
                    f"#### {nombre} {badge_html(clasificacion['status_text'], clasificacion['status_type'])}",
                    unsafe_allow_html=True,
                )

                sensores_count = len(df_sensores)
                last_ts = clasificacion["last_ts"]
                last_text = tiempo_relativo(last_ts)
                ts_text = last_ts.strftime("%Y-%m-%d %H:%M:%S") if pd.notna(last_ts) else "No disponible"

                st.markdown(
                    f"""
                    <div class="subtle">
                        ID: <b>{ambiente_id}</b> &nbsp;&nbsp;|&nbsp;&nbsp;
                        Sensores: <b>{sensores_count}</b> &nbsp;&nbsp;|&nbsp;&nbsp;
                        Última telemetría: <b>{ts_text}</b> ({last_text})
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.divider()

                if df_sensores.empty:
                    st.info("Sin telemetría actual.")
                    continue

                c1, c2, c3 = st.columns(3)

                with c1:
                    st.metric(
                        "🌡️ Temperatura media",
                        formatear_valor(resumen["temperatura"]["avg"], "temperatura"),
                    )
                    st.caption(
                        f"Rango sensores: {formatear_rango(resumen['temperatura']['min'], resumen['temperatura']['max'], 'temperatura')} · {resumen['temperatura']['label']}"
                    )

                with c2:
                    st.metric(
                        "💧 Humedad media",
                        formatear_valor(resumen["humedad"]["avg"], "humedad"),
                    )
                    st.caption(
                        f"Rango sensores: {formatear_rango(resumen['humedad']['min'], resumen['humedad']['max'], 'humedad')} · {resumen['humedad']['label']}"
                    )

                with c3:
                    st.metric(
                        "☁️ CO₂ medio",
                        formatear_valor(resumen["co2"]["avg"], "co2"),
                    )
                    st.caption(
                        f"Rango sensores: {formatear_rango(resumen['co2']['min'], resumen['co2']['max'], 'co2')} · {resumen['co2']['label']}"
                    )

                st.caption("Estado de actuadores")
                st.markdown(
                    (
                        actuator_pill("Calefactor", actuadores.get("calefactor", False), "🔥")
                        + actuator_pill("Extractor", actuadores.get("extractor", False), "💨")
                        + actuator_pill("Nebulizador", actuadores.get("nebulizador", False), "💦")
                    ),
                    unsafe_allow_html=True,
                )

                if clasificacion["alerts"]:
                    st.warning(" | ".join(clasificacion["alerts"]))
                else:
                    st.success("Ambiente en rango y sensores reportando correctamente.")

                with st.expander("Ver detalle por sensor"):
                    detalle = df_sensores.copy()

                    detalle["temp_estado"] = detalle["temperatura"].apply(
                        lambda x: evaluar_serie("temperatura", pd.Series([x]))[0] if pd.notna(x) else "Sin dato"
                    )
                    detalle["hum_estado"] = detalle["humedad"].apply(
                        lambda x: evaluar_serie("humedad", pd.Series([x]))[0] if pd.notna(x) else "Sin dato"
                    )
                    detalle["co2_estado"] = detalle["co2"].apply(
                        lambda x: evaluar_serie("co2", pd.Series([x]))[0] if pd.notna(x) else "Sin dato"
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