import os
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
TIMEOUT = 12


class BackendError(Exception):
    pass


# ---------------------------
# Helpers HTTP
# ---------------------------

def _request(method: str, path: str, *, params: Optional[Dict[str, Any]] = None) -> Any:
    url = f"{BACKEND_URL}{path}"
    try:
        response = requests.request(method, url, params=params, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise BackendError(f"No se pudo consultar {url}: {exc}") from exc

    try:
        return response.json()
    except ValueError as exc:
        raise BackendError(f"La respuesta de {url} no es JSON válido.") from exc


# ---------------------------
# Helpers de normalización
# ---------------------------

def _pick(data: Dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in data and data[key] is not None:
            return data[key]
    return default



def _extract_list(payload: Any, *candidate_keys: str) -> List[Dict[str, Any]]:
    if payload is None:
        return []

    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        for key in candidate_keys:
            value = payload.get(key)
            if isinstance(value, list):
                return value

        # fallback común: primer valor tipo lista dentro del dict
        for value in payload.values():
            if isinstance(value, list):
                return value

    return []



def _normalize_ambiente(raw: Dict[str, Any]) -> Dict[str, Any]:
    ambiente_id = _pick(raw, "ambiente_id", "id", "ambienteId", "codigo")
    codigo = _pick(raw, "codigo", "code")
    nombre = _pick(raw, "nombre", "name", default=f"Ambiente {ambiente_id}")
    tipo = _pick(raw, "tipo", "type")
    descripcion = _pick(raw, "descripcion", "description")
    activo = _pick(raw, "activo", "state", "status", default=True)

    return {
        "ambiente_id": ambiente_id,
        "id": ambiente_id,
        "codigo": codigo,
        "nombre": nombre,
        "tipo": tipo,
        "descripcion": descripcion,
        "activo": activo,
    }



def _normalize_sensor(raw: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "sensor_id": _pick(raw, "sensor_id", "id", "sensorId", "codigo"),
        "temperatura": _pick(raw, "temperatura", "temperature", "temp", "t"),
        "humedad": _pick(raw, "humedad", "humedad_relativa", "humidity", "hr", "rh"),
        "co2": _pick(raw, "co2", "CO2", "eco2", "eCO2", "co2_ppm", "co2eq"),
        "estado_sensor": _pick(raw, "estado_sensor", "estado", "status", default="DESCONOCIDO"),
        "timestamp": _pick(raw, "timestamp", "fecha_hora", "fecha", "created_at", "updated_at"),
    }



def _normalize_actuadores(raw: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(raw, dict):
        raw = {}

    return {
        "calefactor": bool(_pick(raw, "calefactor", "heater", "calentador", default=False)),
        "extractor": bool(_pick(raw, "extractor", "ventilador", "fan", "extractor_aire", default=False)),
        "nebulizador": bool(_pick(raw, "nebulizador", "humidificador", "humidifier", "riego", default=False)),
        **raw,
    }



def _normalize_estado_ambiente(raw: Dict[str, Any]) -> Dict[str, Any]:
    ambiente_id = _pick(raw, "ambiente_id", "id", "ambienteId", "ambiente")

    sensores_raw = raw.get("sensores")
    if not isinstance(sensores_raw, list):
        sensores_raw = raw.get("sensor_data")
    if not isinstance(sensores_raw, list):
        sensores_raw = raw.get("mediciones")

    sensores: List[Dict[str, Any]] = []
    if isinstance(sensores_raw, list):
        sensores = [_normalize_sensor(s) for s in sensores_raw if isinstance(s, dict)]
    else:
        sensor_inline = _normalize_sensor(raw)
        if any(sensor_inline.get(k) is not None for k in ("temperatura", "humedad", "co2", "sensor_id", "timestamp")):
            sensores = [sensor_inline]

    actuadores_raw = raw.get("actuadores") if isinstance(raw.get("actuadores"), dict) else raw
    actuadores = _normalize_actuadores(actuadores_raw)

    return {
        "ambiente_id": ambiente_id,
        "sensores": sensores,
        "actuadores": actuadores,
        "timestamp": _pick(raw, "timestamp", "fecha_hora", "updated_at"),
    }



def _normalize_historial_item(raw: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "timestamp": _pick(raw, "timestamp", "fecha_hora", "fecha", "created_at", "updated_at"),
        "ambiente_id": _pick(raw, "ambiente_id", "id_ambiente", "ambienteId", "ambiente", "id"),
        "sensor_id": _pick(raw, "sensor_id", "sensorId", "id_sensor"),
        "temperatura": _pick(raw, "temperatura", "temperature", "temp", "t"),
        "humedad": _pick(raw, "humedad", "humedad_relativa", "humidity", "hr", "rh"),
        "co2": _pick(raw, "co2", "CO2", "eco2", "eCO2", "co2_ppm", "co2eq"),
        "estado_sensor": _pick(raw, "estado_sensor", "estado", "status"),
    }


# ---------------------------
# API pública
# ---------------------------

def get_ambientes() -> List[Dict[str, Any]]:
    payload = _request("GET", "/ambientes")
    ambientes_raw = _extract_list(payload, "ambientes", "data", "items")
    if not ambientes_raw and isinstance(payload, dict):
        ambientes_raw = [payload]
    return [_normalize_ambiente(a) for a in ambientes_raw if isinstance(a, dict)]



def get_estados_ambientes() -> List[Dict[str, Any]]:
    try:
        payload = _request("GET", "/ambientes/estado")
        estados_raw = _extract_list(payload, "estados", "data", "items")
        if not estados_raw and isinstance(payload, dict):
            estados_raw = [payload]
        return [_normalize_estado_ambiente(e) for e in estados_raw if isinstance(e, dict)]
    except BackendError:
        # Fallback útil cuando el endpoint agregado no existe todavía.
        estados: List[Dict[str, Any]] = []
        for ambiente in get_ambientes():
            try:
                estados.append(get_estado_ambiente(ambiente["ambiente_id"]))
            except BackendError:
                estados.append({
                    "ambiente_id": ambiente["ambiente_id"],
                    "sensores": [],
                    "actuadores": _normalize_actuadores({}),
                })
        return estados



def get_ambiente(ambiente_id: Any) -> Dict[str, Any]:
    payload = _request("GET", f"/ambientes/{ambiente_id}")
    if isinstance(payload, dict) and any(k in payload for k in ("ambiente_id", "id", "nombre", "codigo")):
        return _normalize_ambiente(payload)

    ambientes = _extract_list(payload, "ambientes", "data", "items")
    if ambientes:
        return _normalize_ambiente(ambientes[0])

    raise BackendError(f"No se pudo interpretar la respuesta del ambiente {ambiente_id}.")



def get_estado_ambiente(ambiente_id: Any) -> Dict[str, Any]:
    payload = _request("GET", f"/ambientes/{ambiente_id}/estado")
    if isinstance(payload, dict):
        normalized = _normalize_estado_ambiente(payload)
        if normalized["ambiente_id"] is None:
            normalized["ambiente_id"] = ambiente_id
        return normalized

    estados_raw = _extract_list(payload, "estados", "data", "items")
    if estados_raw:
        normalized = _normalize_estado_ambiente(estados_raw[0])
        if normalized["ambiente_id"] is None:
            normalized["ambiente_id"] = ambiente_id
        return normalized

    return {
        "ambiente_id": ambiente_id,
        "sensores": [],
        "actuadores": _normalize_actuadores({}),
    }



def get_historial_ambiente(ambiente_id: Any, variable: Optional[str] = None, limite: int = 200) -> List[Dict[str, Any]]:
    params: Dict[str, Any] = {"limite": limite}
    if variable:
        params["variable"] = variable

    payload = _request("GET", f"/ambientes/{ambiente_id}/historial", params=params)
    historial_raw = _extract_list(payload, "historial", "data", "items", "registros")
    return [_normalize_historial_item(item) for item in historial_raw if isinstance(item, dict)]



def get_historial_global(variable: Optional[str] = None, limite: int = 200, desde: Optional[str] = None, hasta: Optional[str] = None) -> List[Dict[str, Any]]:
    params: Dict[str, Any] = {"limite": limite}
    if variable:
        params["variable"] = variable
    if desde:
        params["desde"] = desde
    if hasta:
        params["hasta"] = hasta

    payload = _request("GET", "/historial_sensores", params=params)
    historial_raw = _extract_list(payload, "historial", "data", "items", "registros")
    return [_normalize_historial_item(item) for item in historial_raw if isinstance(item, dict)]



def get_ultima_clasificacion() -> Dict[str, Any]:
    payload = _request("GET", "/ultima_analisis")
    return payload if isinstance(payload, dict) else {"data": payload}
