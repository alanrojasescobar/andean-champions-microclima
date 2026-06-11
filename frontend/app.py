from pathlib import Path

import streamlit as st

from api.client import BACKEND_URL, BackendError, get_ambientes
from components.header import render_header

st.set_page_config(
    page_title="Sistema de Monitoreo Ambiental",
    page_icon="🧪",
    layout="wide",
)


def verificar_backend():
    try:
        ambientes = get_ambientes()
        return True, f"Conectado correctamente a {BACKEND_URL}. Ambientes detectados: {len(ambientes)}"
    except BackendError as exc:
        return False, str(exc)


render_header("Sistema de Monitoreo y Supervisión Ambiental")

st.markdown(
    """
Este frontend fue ajustado para consumir el backend de monitoreo de forma más robusta.
Acepta respuestas con campos como `id` o `ambiente_id`, y también tolera diferencias de
nombres en sensores y actuadores.
"""
)

st.subheader("Estado de conexión del sistema")
ok, mensaje = verificar_backend()
if ok:
    st.success(mensaje)
else:
    st.error(mensaje)

st.subheader("Módulos disponibles")
col1, col2 = st.columns(2)

with col1:
    st.info(
        """
**Dashboard**  
Vista general del estado actual de todos los ambientes registrados.
"""
    )
    st.info(
        """
**Ambientes**  
Detalle por ambiente con estado, actuadores e historial.
"""
    )

with col2:
    st.info(
        """
**Histórico Global**  
Consulta transversal de registros del sistema completo.
"""
    )
    st.info(
        """
**Estadísticas**  
Resumen estadístico a partir del historial almacenado.
"""
    )

st.subheader("Estructura esperada del proyecto")
st.code(
    """frontend_corregido/
├── app.py
├── api/
│   └── client.py
├── components/
│   ├── header.py
│   └── charts.py
└── pages/
    ├── 1_Dashboard.py
    ├── 2_Ambientes.py
    ├── 3_Historico_Global.py
    └── 4_Estadisticas.py
"""
)

if not Path(".env").exists():
    st.warning("No se encontró archivo .env en esta carpeta. Define BACKEND_URL para apuntar a tu API.")