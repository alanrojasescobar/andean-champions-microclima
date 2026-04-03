from fastapi import FastAPI, HTTPException, Query, Header, Depends, status
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal, List, Dict
import logging
import os
from dotenv import load_dotenv

from app.controlador import ControladorAmbiente

load_dotenv()

# ===================== LOGGING =====================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===================== CONFIG =====================
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = int(os.getenv("PG_PORT", "5432"))
PG_DBNAME = os.getenv("PG_DBNAME", "tesis_microclima")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "")

API_KEY_RPI = os.getenv("API_KEY_RPI", "")
ENV = os.getenv("ENV", "development")
# ===================== MEMORIA =====================
estado_actual_por_ambiente: Dict[str, dict] = {}

# ===================== APP =====================
app = FastAPI(
    title="API de Monitoreo Ambiental",
    description="Backend modular para monitoreo y supervisión de ambientes de cultivo",
    version="3.0.0"
)

controlador = ControladorAmbiente(
    host=PG_HOST,
    port=PG_PORT,
    dbname=PG_DBNAME,
    user=PG_USER,
    password=PG_PASSWORD,
)

# ===================== MODELOS DE ENTRADA =====================
class EventoTelemetria(BaseModel):
    ambiente_id: str = Field(..., description="Código del ambiente, por ejemplo SF-2")
    sensor_id: str = Field(..., description="Código del punto de medición, por ejemplo A")
    temperatura: Optional[float] = None
    humedad: Optional[float] = None
    co2: Optional[float] = None
    estado_calefactor: bool
    estado_extractor: bool
    estado_nebulizador: bool
    timestamp: datetime
    estado_sensor: Literal["OK", "ERROR", "DESCONEXION"]


# ===================== MODELOS DE SALIDA =====================
class AmbienteResponse(BaseModel):
    ambiente_id: str
    nombre: str
    tipo: Optional[str] = None
    ubicacion: Optional[str] = None
    descripcion: Optional[str] = None
    activo: bool = True


class SensorEstadoResponse(BaseModel):
    sensor_id: str
    temperatura: Optional[float] = None
    humedad: Optional[float] = None
    co2: Optional[float] = None
    estado_sensor: Literal["OK", "ERROR", "DESCONEXION"]
    timestamp: datetime


class ActuadoresEstadoResponse(BaseModel):
    calefactor: bool
    extractor: bool
    nebulizador: bool


class EstadoAmbienteResponse(BaseModel):
    ambiente_id: str
    sensores: List[SensorEstadoResponse]
    actuadores: ActuadoresEstadoResponse
    ultima_actualizacion: datetime


class RegistroHistoricoResponse(BaseModel):
    ambiente_id: str
    sensor_id: str
    temperatura: Optional[float] = None
    humedad: Optional[float] = None
    co2: Optional[float] = None
    estado_calefactor: bool
    estado_extractor: bool
    estado_nebulizador: bool
    estado_sensor: Literal["OK", "ERROR", "DESCONEXION"]
    timestamp: datetime


class MensajeResponse(BaseModel):
    status: str
    message: str
def verificar_api_key_rpi(x_api_key: str = Header(...)):
    if not API_KEY_RPI:
        logger.error("API_KEY_RPI no está configurada en el entorno.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Configuración de seguridad incompleta"
        )

    if x_api_key != API_KEY_RPI:
        logger.warning("Intento de acceso con API key inválida en /telemetria")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key inválida"
        )

# ===================== EVENTOS =====================
@app.on_event("startup")
async def startup_event():
    try:
        logger.info("Iniciando servidor de telemetría...")
        controlador.verificar_conexion()
        logger.info("Conexión con PostgreSQL establecida correctamente.")
    except Exception as e:
        logger.error(f"Error al iniciar la aplicación: {e}")


# ===================== FUNCIONES AUXILIARES =====================
def construir_estado_ambiente(data: EventoTelemetria):
    """
    Actualiza el cache en memoria del estado actual por ambiente.
    Soporta múltiples puntos de medición por ambiente.
    """
    ambiente_id = data.ambiente_id

    if ambiente_id not in estado_actual_por_ambiente:
        estado_actual_por_ambiente[ambiente_id] = {
            "ambiente_id": ambiente_id,
            "sensores": {},
            "actuadores": {
                "calefactor": data.estado_calefactor,
                "extractor": data.estado_extractor,
                "nebulizador": data.estado_nebulizador,
            },
            "ultima_actualizacion": data.timestamp,
        }

    estado_actual_por_ambiente[ambiente_id]["sensores"][data.sensor_id] = {
        "sensor_id": data.sensor_id,
        "temperatura": data.temperatura,
        "humedad": data.humedad,
        "co2": data.co2,
        "estado_sensor": data.estado_sensor,
        "timestamp": data.timestamp,
    }

    estado_actual_por_ambiente[ambiente_id]["actuadores"] = {
        "calefactor": data.estado_calefactor,
        "extractor": data.estado_extractor,
        "nebulizador": data.estado_nebulizador,
    }

    estado_actual_por_ambiente[ambiente_id]["ultima_actualizacion"] = data.timestamp


def serializar_estado_ambiente(estado: dict) -> dict:
    sensores_list = []
    for sensor in estado["sensores"].values():
        sensores_list.append(
            {
                "sensor_id": sensor["sensor_id"],
                "temperatura": sensor["temperatura"],
                "humedad": sensor["humedad"],
                "co2": sensor["co2"],
                "estado_sensor": sensor["estado_sensor"],
                "timestamp": sensor["timestamp"],
            }
        )

    return {
        "ambiente_id": estado["ambiente_id"],
        "sensores": sensores_list,
        "actuadores": estado["actuadores"],
        "ultima_actualizacion": estado["ultima_actualizacion"],
    }


# ===================== ENDPOINTS ESTADO ACTUAL =====================
# Importante: las rutas fijas van antes que /ambientes/{ambiente_id}
@app.get("/ambientes/estado", response_model=List[EstadoAmbienteResponse])
def listar_estado_actual():
    try:
        return [
            serializar_estado_ambiente(estado)
            for estado in estado_actual_por_ambiente.values()
        ]
    except Exception as e:
        logger.error(f"Error al consultar estados actuales: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ambientes/{ambiente_id}/estado", response_model=EstadoAmbienteResponse)
def obtener_estado_actual_ambiente(ambiente_id: str):
    if ambiente_id not in estado_actual_por_ambiente:
        raise HTTPException(status_code=404, detail="No existe estado actual para este ambiente")

    try:
        return serializar_estado_ambiente(estado_actual_por_ambiente[ambiente_id])
    except Exception as e:
        logger.error(f"Error al consultar estado actual del ambiente {ambiente_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===================== ENDPOINTS ESTRUCTURA =====================
@app.get("/ambientes", response_model=List[AmbienteResponse])
def listar_ambientes():
    try:
        return controlador.obtener_ambientes()
    except Exception as e:
        logger.error(f"Error al listar ambientes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ambientes/{ambiente_id}", response_model=AmbienteResponse)
def obtener_ambiente(ambiente_id: str):
    try:
        ambiente = controlador.obtener_ambiente_por_id(ambiente_id)
        if not ambiente:
            raise HTTPException(status_code=404, detail="Ambiente no encontrado")
        return ambiente
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al consultar ambiente {ambiente_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===================== ENDPOINT TELEMETRÍA =====================
@app.post("/telemetria", response_model=MensajeResponse)
async def registrar_telemetria(
    data: EventoTelemetria,
    _: None = Depends(verificar_api_key_rpi)
):
    try:
        if data.estado_sensor == "ERROR":
            logger.warning(
                f"Sensor con falla: sensor={data.sensor_id}, ambiente={data.ambiente_id}"
            )

        if data.estado_sensor == "DESCONEXION":
            logger.warning(
                f"Sensor desconectado: sensor={data.sensor_id}, ambiente={data.ambiente_id}"
            )

        construir_estado_ambiente(data)

        controlador.guardar_evento_en_db(
            ambiente_id=data.ambiente_id,
            sensor_id=data.sensor_id,
            temperatura=data.temperatura,
            humedad=data.humedad,
            co2=data.co2,
            estado_calefactor=data.estado_calefactor,
            estado_extractor=data.estado_extractor,
            estado_nebulizador=data.estado_nebulizador,
            timestamp=data.timestamp,
            estado_sensor=data.estado_sensor,
        )

        return {
            "status": "registrado",
            "message": "Telemetría almacenada correctamente",
        }

    except ValueError as e:
        logger.error(f"Datos inválidos al registrar telemetría: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error al registrar telemetría: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===================== ENDPOINTS HISTORIAL =====================
@app.get("/ambientes/{ambiente_id}/historial", response_model=List[RegistroHistoricoResponse])
def obtener_historial_ambiente(
    ambiente_id: str,
    variable: Optional[Literal["temperatura", "humedad", "co2"]] = Query(None),
    limite: int = Query(200, ge=1, le=5000),
    desde: Optional[datetime] = Query(None),
    hasta: Optional[datetime] = Query(None),
):
    try:
        historial = controlador.obtener_historial_sensores(
            ambiente_id=ambiente_id,
            variable=variable,
            limite=limite,
            desde=desde,
            hasta=hasta,
        )

        if historial is None:
            raise HTTPException(status_code=404, detail="Ambiente no encontrado")

        return historial
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al consultar historial del ambiente {ambiente_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/historial_sensores", response_model=List[RegistroHistoricoResponse])
def obtener_historial_global(
    variable: Optional[Literal["temperatura", "humedad", "co2"]] = Query(None),
    limite: int = Query(200, ge=1, le=5000),
    desde: Optional[datetime] = Query(None),
    hasta: Optional[datetime] = Query(None),
):
    try:
        return controlador.obtener_historial_sensores(
            ambiente_id=None,
            variable=variable,
            limite=limite,
            desde=desde,
            hasta=hasta,
        )
    except Exception as e:
        logger.error(f"Error al consultar historial global: {e}")
        raise HTTPException(status_code=500, detail=str(e))