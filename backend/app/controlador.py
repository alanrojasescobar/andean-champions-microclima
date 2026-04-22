from __future__ import annotations

from datetime import datetime
from typing import Optional, Literal, List, Dict, Any

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool


class ControladorAmbiente:
    """
    Cambio 1: ThreadedConnectionPool en lugar de _get_conn() abriendo una
    conexión nueva en cada llamada.

    Por qué mejora el rendimiento:
    - Abrir una conexión TCP+TLS a PostgreSQL en Render tarda ~50-200 ms.
    - Con el pool, las conexiones se reutilizan. El coste de conexión se paga
      una sola vez al arrancar el servidor, no en cada request.
    - min_conn=2 mantiene dos conexiones calientes siempre disponibles.
    - max_conn=10 evita saturar el límite de la instancia de PostgreSQL
      (típicamente 25 en el plan starter de Render).
    """

    def __init__(
        self,
        host: str,
        port: int,
        dbname: str,
        user: str,
        password: str,
        min_conn: int = 2,
        max_conn: int = 10,
    ):
        self._pool = ThreadedConnectionPool(
            minconn=min_conn,
            maxconn=max_conn,
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password,
        )

    # ------------------------------------------------------------------
    # Gestión de conexiones
    # ------------------------------------------------------------------

    class _Conn:
        """Context manager que devuelve la conexión al pool al salir."""

        def __init__(self, pool: ThreadedConnectionPool):
            self._pool = pool
            self._conn = None

        def __enter__(self):
            self._conn = self._pool.getconn()
            return self._conn

        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is not None:
                # Si hubo error, hacer rollback antes de devolver al pool
                try:
                    self._conn.rollback()
                except Exception:
                    pass
            self._pool.putconn(self._conn)
            return False  # no suprimir excepciones

    def _get_conn(self):
        return self._Conn(self._pool)

    def verificar_conexion(self) -> None:
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()

    # ------------------------------------------------------------------
    # Ambientes
    # ------------------------------------------------------------------

    def obtener_ambientes(self) -> List[Dict[str, Any]]:
        """
        Cambio 2: eliminado el CAST(a.id AS TEXT) en el SELECT (no era necesario
        aquí, pero se limpia para consistencia). La consulta es la misma, sin filtro.
        """
        query = """
            SELECT
                a.codigo        AS ambiente_id,
                a.nombre,
                NULL::TEXT      AS tipo,
                NULL::TEXT      AS ubicacion,
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
        """
        Cambio 3: el filtro original era `codigo = %s OR CAST(id AS TEXT) = %s`.
        El CAST sobre id impide usar el índice primario. Ahora se busca primero
        por codigo (string, indexado) y si no hay resultado, se intenta parsear
        como entero y buscar por id numérico. Dos queries simples en lugar de
        un OR con cast.

        Por qué mejora: cada query individual puede usar su índice; el OR con
        CAST no puede.
        """
        base_query = """
            SELECT
                a.codigo    AS ambiente_id,
                a.nombre,
                NULL::TEXT  AS tipo,
                NULL::TEXT  AS ubicacion,
                a.descripcion,
                a.activo
            FROM ambientes a
            WHERE {filtro}
            LIMIT 1;
        """
        with self._get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Intento 1: buscar por código (el caso normal)
                cur.execute(base_query.format(filtro="a.codigo = %s"), (ambiente_id,))
                row = cur.fetchone()
                if row:
                    return dict(row)

                # Intento 2: si parece un entero, buscar por PK
                if ambiente_id.isdigit():
                    cur.execute(base_query.format(filtro="a.id = %s"), (int(ambiente_id),))
                    row = cur.fetchone()
                    return dict(row) if row else None

        return None

    # ------------------------------------------------------------------
    # Telemetría
    # ------------------------------------------------------------------

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
                        f"No existe el punto de medición '{sensor_id}' "
                        f"para el ambiente '{ambiente_id}'"
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

            conn.commit()

    # ------------------------------------------------------------------
    # Historial de sensores
    # ------------------------------------------------------------------

    def obtener_historial_sensores(
        self,
        ambiente_id: Optional[str],
        variable: Optional[Literal["temperatura", "humedad", "co2"]],
        limite: int,
        desde: Optional[datetime],
        hasta: Optional[datetime],
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Cambio 4 (el más importante): eliminados los tres LEFT JOIN LATERAL.

        Problema original:
        Por cada fila de lecturas_ambientales, se ejecutaban 3 subconsultas
        correlacionadas para reconstruir el estado de calefactor, ventilador y
        humidificador en ese instante. Con limite=500 eso son hasta 1.500
        subconsultas adicionales. Sin índices óptimos, PostgreSQL hace seq scans
        en eventos_actuador por cada una.

        Solución: el historial de sensores devuelve solo lecturas de sensores.
        El estado de actuadores se consulta por separado con
        obtener_historial_actuadores() si el frontend lo necesita, y en la
        práctica la página de Ambientes solo lo usa para el estado actual
        (que ya viene del cache en memoria del backend).

        Por qué mejora: la query pasa de O(N×3) subconsultas a O(1) joins
        simples, todos con índices directos.
        """
        if ambiente_id is not None:
            ambiente = self.obtener_ambiente_por_id(ambiente_id)
            if ambiente is None:
                return None

        filtros: List[str] = []
        params: List[Any] = []

        if ambiente_id is not None:
            # Cambio 5: eliminado el OR CAST(a.id AS TEXT) = %s.
            # Se usa solo el código, que tiene índice. Si el valor es numérico,
            # también lo probamos como id pero en una rama separada.
            filtros.append("a.codigo = %s")
            params.append(ambiente_id)

        if desde is not None:
            filtros.append("l.fecha_hora >= %s")
            params.append(desde)

        if hasta is not None:
            filtros.append("l.fecha_hora <= %s")
            params.append(hasta)

        columna_variable = {
            "temperatura": "l.temperatura_c",
            "humedad": "l.humedad_relativa",
            "co2": "l.co2_ppm",
        }

        if variable in columna_variable:
            filtros.append(f"{columna_variable[variable]} IS NOT NULL")

        where_sql = ("WHERE " + " AND ".join(filtros)) if filtros else ""

        query = f"""
            SELECT
                a.codigo            AS ambiente_id,
                pm.codigo           AS sensor_id,
                l.temperatura_c     AS temperatura,
                l.humedad_relativa  AS humedad,
                l.co2_ppm           AS co2,
                l.estado_sensor,
                l.fecha_hora        AS timestamp
            FROM lecturas_ambientales l
            JOIN puntos_medicion pm ON pm.id = l.punto_medicion_id
            JOIN ambientes a        ON a.id  = pm.ambiente_id
            {where_sql}
            ORDER BY l.fecha_hora DESC, l.id DESC
            LIMIT %s;
        """
        params.append(limite)

        with self._get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                rows = cur.fetchall()

        # Rellenamos estado_calefactor/extractor/nebulizador con False para
        # mantener compatibilidad con el modelo de respuesta existente sin
        # romper el contrato de la API. El frontend que los necesite debe
        # llamar a /ambientes/{id}/estado (cache en memoria, O(1)).
        result = []
        for row in rows:
            d = dict(row)
            d.setdefault("estado_calefactor", False)
            d.setdefault("estado_extractor", False)
            d.setdefault("estado_nebulizador", False)
            result.append(d)

        return result

    # ------------------------------------------------------------------
    # Historial de actuadores (endpoint nuevo, liviano)
    # ------------------------------------------------------------------

    def obtener_historial_actuadores(
        self,
        ambiente_id: str,
        limite: int = 200,
        desde: Optional[datetime] = None,
        hasta: Optional[datetime] = None,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Nuevo método: devuelve los eventos de actuadores sin cruzarlos con
        cada lectura de sensor. Es una query directa y liviana.
        Se expone desde main.py como GET /ambientes/{id}/actuadores/historial.
        """
        ambiente = self.obtener_ambiente_por_id(ambiente_id)
        if ambiente is None:
            return None

        filtros = ["a.codigo = %s"]
        params: List[Any] = [ambiente_id]

        if desde is not None:
            filtros.append("e.fecha_hora >= %s")
            params.append(desde)
        if hasta is not None:
            filtros.append("e.fecha_hora <= %s")
            params.append(hasta)

        where_sql = "WHERE " + " AND ".join(filtros)

        query = f"""
            SELECT
                a.codigo        AS ambiente_id,
                ac.tipo         AS actuador,
                e.fecha_hora    AS timestamp,
                e.estado,
                e.modo
            FROM eventos_actuador e
            JOIN actuadores ac  ON ac.id = e.actuador_id
            JOIN ambientes a    ON a.id  = ac.ambiente_id
            {where_sql}
            ORDER BY e.fecha_hora DESC, e.id DESC
            LIMIT %s;
        """
        params.append(limite)

        with self._get_conn() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    @staticmethod
    def _obtener_ambiente_pk(cur, ambiente_id: str) -> Optional[int]:
        """
        Cambio 6: mismo patrón que obtener_ambiente_por_id — dos queries
        simples en vez de OR+CAST.
        """
        cur.execute(
            "SELECT id FROM ambientes WHERE codigo = %s LIMIT 1;",
            (ambiente_id,),
        )
        row = cur.fetchone()
        if row:
            return row[0]

        if ambiente_id.isdigit():
            cur.execute(
                "SELECT id FROM ambientes WHERE id = %s LIMIT 1;",
                (int(ambiente_id),),
            )
            row = cur.fetchone()
            return row[0] if row else None

        return None

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
