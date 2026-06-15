import streamlit as st


def load_css(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        css = f.read()

    st.markdown(
        f"<style>{css}</style>",
        unsafe_allow_html=True
    )