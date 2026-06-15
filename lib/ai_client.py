import streamlit as st
from openai import OpenAI


@st.cache_resource
def get_ai_client():
    try:
        api_key = st.secrets["DEEPSEEK_API_KEY"]

        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )

        return client, True

    except Exception:
        return None, False