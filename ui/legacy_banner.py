"""Banner for LEGACY nav pages."""

import streamlit as st


def render_legacy_banner() -> None:
    st.markdown(
        """
        <div class="mag-legacy-banner">
            LEGACY / REFERENCE — NOT PART OF THE AGENTIC DECISION-GRADE STORY
        </div>
        """,
        unsafe_allow_html=True,
    )
