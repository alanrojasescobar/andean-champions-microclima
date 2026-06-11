from datetime import datetime
from pathlib import Path

import streamlit as st


def buscar_logo(rutas):
    return next((p for p in rutas if p.exists()), None)


def render_header(title: str) -> None:
    ahora = datetime.now()

    # Izquierda: UCB | Centro: título | Derecha: empresa
    col_ucb, col_title, col_empresa = st.columns([1.5, 4, 1.7])

    # =========================
    # Logo UCB - izquierda
    # =========================
    with col_ucb:
        rutas_ucb = [
            Path("imagenes/logo_ucb.png"),
            Path("assets/UCB_logo.png"),
            Path("logo_ucb.png"),
        ]
        logo_ucb = buscar_logo(rutas_ucb)

        if logo_ucb:
            st.image(str(logo_ucb), width=100)
        else:
            st.markdown(
                """
                <div style="
                    height:70px;
                    display:flex;
                    align-items:center;
                    justify-content:flex-start;
                    font-weight:800;
                    color:#1E3A8A;
                    font-size:0.85rem;
                ">
                    LOGO UCB
                </div>
                """,
                unsafe_allow_html=True,
            )

    # =========================
    # Título y fecha - centro
    # =========================
    with col_title:
        st.markdown(
            f"""
            <div style="
                text-align:center;
                color:#6B7280;
                font-size:0.82rem;
                margin-top:0.15rem;
            ">
                {ahora.strftime('%d/%m/%Y %H:%M:%S')}
            </div>

            <h1 style="
                text-align:center;
                margin-top:0.25rem;
                margin-bottom:0;
                font-size:2rem;
                color:#0F172A;
                font-weight:800;
                line-height:1.15;
            ">
                {title}
            </h1>
            """,
            unsafe_allow_html=True,
        )

    # =========================
    # Logo empresa - derecha
    # =========================
    with col_empresa:
        rutas_empresa = [
            Path("imagenes/logoB.png"),
            Path("assets/logoB.png"),
            Path("logoB.png"),
        ]
        logo_empresa = buscar_logo(rutas_empresa)

        if logo_empresa:
            st.image(str(logo_empresa), width=170)
        else:
            st.markdown(
                """
                <div style="
                    height:70px;
                    display:flex;
                    align-items:center;
                    justify-content:center;
                ">
                    <svg width="52" height="52" viewBox="0 0 24 24" fill="none"
                         stroke="#D4AF37" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M4 11C4 6.6 7.6 3 12 3s8 3.6 8 8H4z"/>
                        <path d="M8 11h8"/>
                        <path d="M10 11c0 2.5-.8 4.5-2 7h8c-1.2-2.5-2-4.5-2-7"/>
                        <path d="M7 8.5h.01"/>
                        <path d="M12 6.5h.01"/>
                        <path d="M17 8.5h.01"/>
                    </svg>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()