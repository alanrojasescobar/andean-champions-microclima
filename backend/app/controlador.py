from __future__ import annotations

from datetime import datetime
from typing import Optional, Literal, List, Dict, Any

import psycopg2
from psycopg2.extras import RealDictCursor


class ControladorAmbiente:
    def __init__(self, host: str, port: int, dbname: str, user: str, password: str):
        self._conn_kwargs = {
            "host": host,
            "port": port,
            "dbname": dbname,
            "user": user,
            "password": password,
        }

    def _get_conn(self):
        return psycopg2.connect(**self._conn_kwargs)

    def verificar_conexion(self) -> None:
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()

    def obtener_ambientes(self) -> List[Dict[str, Any]]:
        query = """
            SELECT
                a.codigo AS ambiente_id,
                a.nombre,
                NULL::TEXT AS tipo,
                NULL::TEXT AS ubicacion,
                a.descripcion,
                a.activo
            FROM ambientes a
            ORDER BY a.codigo;
        """
        with self._get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                return [dict(row) for row in cur.fetchall()]

    def obtener_ambiente_por_id(self, ambiente_id: str) -> Optional[Dict[str, Any]]:
        query = """
            SELECT
                a.codigo AS ambiente_id,
                a.nombre,
                NULL::TEXT AS tipo,
                NULL::TEXT AS ubicacion,
                a.descripcion,
                a.activo
            FROM ambientes a
            WHERE a.codigo = %s OR CAST(a.id AS TEXT) = %s
            LIMIT 1;
        """
        with self._get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, (ambiente_id, ambiente_id))
                row = cur.fetchone()
                return dict(row) if row else None

    def guardar_evento_en_db(
        self,
        ambiente_id: str,
        sensor_id: str,
        temperatura: Optional[float],
        humedad: Optional[float],
        co2: Optional[float],
        estado_calefactor: bool,
        estado_extractor: bool,
        estado_nebulizador: bool,
        timestamp: datetime,
        estado_sensor: str,
    ) -> None:
        if estado_sensor not in {"OK", "ERROR", "DESCONEXION"}:
            raise ValueError("estado_sensor no válido")

        with self._get_conn() as conn:
            with conn.cursor() as cur:
                ambiente_pk = self._obtener_ambiente_pk(cur, ambiente_id)
                if ambiente_pk is None:
                    raise ValueError(f"No existe el ambiente '{ambiente_id}'")

                punto_pk = self._obtener_punto_pk(cur, ambiente_pk, sensor_id)
                if punto_pk is None:
                    raise ValueError(
                        f"No existe el punto de medición '{sensor_id}' para el ambiente '{ambiente_id}'"
                    )

                cur.execute(
                    """
                    INSERT INTO lecturas_ambientales (
                        punto_medicion_id,
                        fecha_hora,
                        temperatura_c,
                        humedad_relativa,
                        co2_ppm,
                        estado_sensor
                    )
                    VALUES (%s, %s, %s, %s, %s, %s);
                    """,
                    (
                        punto_pk,
                        timestamp,
                        temperatura,
                        humedad,
                        int(co2) if co2 is not None else None,
                        estado_sensor,
                    ),
                )

                estados_por_tipo = {
                    "calefactor": estado_calefactor,
                    "ventilador": estado_extractor,
                    "humidificador": estado_nebulizador,
                }

                for tipo_actuador, estado_bool in estados_por_tipo.items():
                    actuador_pk = self._obtener_actuador_pk(cur, ambiente_pk, tipo_actuador)
                    if actuador_pk is None:
                        continue

                    nuevo_estado = "ON" if estado_bool else "OFF"
                    ultimo_estado = self._obtener_ultimo_estado_actuador(cur, actuador_pk)

                    if ultimo_estado != nuevo_estado:
                        cur.execute(
                            """
                            INSERT INTO eventos_actuador (
                                actuador_id,
                                fecha_hora,
                                estado,
                                modo
                            )
                            VALUES (%s, %s, %s, %s);
                            """,
                            (actuador_pk, timestamp, nuevo_estado, "AUTO"),
                        )

    def obtener_historial_sensores(
        self,
        ambiente_id: Optional[str],
        variable: Optional[Literal["temperatura", "humedad", "co2"]],
        limite: int,
        desde: Optional[datetime],
        hasta: Optional[datetime],
    ) -> Optional[List[Dict[str, Any]]]:
        if ambiente_id is not None:
            ambiente = self.obtener_ambiente_por_id(ambiente_id)
            if ambiente is None:
                return None

        filtros = []
        params: List[Any] = []

        if ambiente_id is not None:
            filtros.append("(a.codigo = %s OR CAST(a.id AS TEXT) = %s)")
            params.extend([ambiente_id, ambiente_id])

        if desde is not None:
            filtros.append("l.fecha_hora >= %s")
            params.append(desde)

        if hasta is not None:
            filtros.append("l.fecha_hora <= %s")
            params.append(hasta)

        if variable == "temperatura":
            filtros.append("l.temperatura_c IS NOT NULL")
        elif variable == "humedad":
            filtros.append("l.humedad_relativa IS NOT NULL")
        elif variable == "co2":
            filtros.append("l.co2_ppm IS NOT NULL")

        where_sql = ""
        if filtros:
            where_sql = "WHERE " + " AND ".join(filtros)

        query = f"""
            SELECT
                a.codigo AS ambiente_id,
                pm.codigo AS sensor_id,
                l.temperatura_c AS temperatura,
                l.humedad_relativa AS humedad,
                l.co2_ppm AS co2,
                COALESCE(calef.estado = 'ON', FALSE) AS estado_calefactor,
                COALESCE(vent.estado = 'ON', FALSE) AS estado_extractor,
                COALESCE(hum.estado = 'ON', FALSE) AS estado_nebulizador,
                l.estado_sensor,
                l.fecha_hora AS timestamp
            FROM lecturas_ambientales l
            JOIN puntos_medicion pm ON pm.id = l.punto_medicion_id
            JOIN ambientes a ON a.id = pm.ambiente_id
            LEFT JOIN LATERAL (
                SELECT e.estado
                FROM eventos_actuador e
                JOIN actuadores ac ON ac.id = e.actuador_id
                WHERE ac.ambiente_id = a.id
                  AND ac.tipo = 'calefactor'
                  AND e.fecha_hora <= l.fecha_hora
                ORDER BY e.fecha_hora DESC, e.id DESC
                LIMIT 1
            ) calef ON TRUE
            LEFT JOIN LATERAL (
                SELECT e.estado
                FROM eventos_actuador e
                JOIN actuadores ac ON ac.id = e.actuador_id
                WHERE ac.ambiente_id = a.id
                  AND ac.tipo = 'ventilador'
                  AND e.fecha_hora <= l.fecha_hora
                ORDER BY e.fecha_hora DESC, e.id DESC
                LIMIT 1
            ) vent ON TRUE
            LEFT JOIN LATERAL (
                SELECT e.estado
                FROM eventos_actuador e
                JOIN actuadores ac ON ac.id = e.actuador_id
                WHERE ac.ambiente_id = a.id
                  AND ac.tipo = 'humidificador'
                  AND e.fecha_hora <= l.fecha_hora
                ORDER BY e.fecha_hora DESC, e.id DESC
                LIMIT 1
            ) hum ON TRUE
            {where_sql}
            ORDER BY l.fecha_hora DESC, l.id DESC
            LIMIT %s;
        """
        params.append(limite)

        with self._get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]

    @staticmethod
    def _obtener_ambiente_pk(cur, ambiente_id: str) -> Optional[int]:
        cur.execute(
            """
            SELECT id
            FROM ambientes
            WHERE codigo = %s OR CAST(id AS TEXT) = %s
            LIMIT 1;
            """,
            (ambiente_id, ambiente_id),
        )
        row = cur.fetchone()
        return row[0] if row else None

    @staticmethod
    def _obtener_punto_pk(cur, ambiente_pk: int, sensor_id: str) -> Optional[int]:
        cur.execute(
            """
            SELECT id
            FROM puntos_medicion
            WHERE ambiente_id = %s
              AND codigo = %s
              AND activo = TRUE
            LIMIT 1;
            """,
            (ambiente_pk, sensor_id),
        )
        row = cur.fetchone()
        return row[0] if row else None

    @staticmethod
    def _obtener_actuador_pk(cur, ambiente_pk: int, tipo_actuador: str) -> Optional[int]:
        cur.execute(
            """
            SELECT id
            FROM actuadores
            WHERE ambiente_id = %s
              AND tipo = %s
              AND activo = TRUE
            ORDER BY id
            LIMIT 1;
            """,
            (ambiente_pk, tipo_actuador),
        )
        row = cur.fetchone()
        return row[0] if row else None

    @staticmethod
    def _obtener_ultimo_estado_actuador(cur, actuador_pk: int) -> Optional[str]:
        cur.execute(
            """
            SELECT estado
            FROM eventos_actuador
            WHERE actuador_id = %s
            ORDER BY fecha_hora DESC, id DESC
            LIMIT 1;
            """,
            (actuador_pk,),
        )
        row = cur.fetchone()
        return row[0] if row else None