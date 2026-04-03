from datetime import datetime
from pathlib import Path

import streamlit as st


def render_header(title: str) -> None:
    ahora = datetime.now()
    col_logo, col_title = st.columns([1, 5])

    with col_logo:
        possible_paths = [
            Path("imagenes/logoB.png"),
            Path("assets/logoB.png"),
            Path("logoB.png"),
        ]
        logo_path = next((p for p in possible_paths if p.exists()), None)
        if logo_path:
            st.image(str(logo_path), width=120)
        else:
            st.markdown("## 🧪")

    with col_title:
        st.markdown(
            f"<div style='text-align: right; color: gray;'>{ahora.strftime('%d/%m/%Y %H:%M:%S')}</div>",
            unsafe_allow_html=True,
        )
        st.title(title)

    st.divider()
