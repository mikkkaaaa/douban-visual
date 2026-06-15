import streamlit as st
from utils.book_cleaner import clean_books_df


@st.cache_data(ttl=3600, show_spinner="正在从数据库读取图书数据...")
def load_books():
    conn = st.connection("mysql", type="sql")
    df = conn.query("SELECT * FROM books;")
    df = clean_books_df(df)
    return df