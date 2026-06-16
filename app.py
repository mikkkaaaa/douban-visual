import streamlit as st

from lib.database import load_books
from lib.ai_client import get_ai_client
from utils.style_loader import load_css

from components.sidebar import render_book_sidebar
from components.books.overview import render_book_overview
from components.books.charts import render_book_charts
from components.ai.curator import render_curator_chat
from components.ai.data_analyst import render_ai_data_analyst

from components.user.auth import render_auth_sidebar_entry
from components.user.my_library import render_my_library


# ---------- 0. 页面基础配置 ----------
st.set_page_config(
    page_title="豆瓣读书Top250 可视化与 AI 平台",
    layout="wide",
    page_icon="📚"
)

load_css("assets/style.css")


# ---------- 1. 初始化数据和 AI 客户端 ----------
public_df = load_books()
client, api_ready = get_ai_client()


# ---------- 2. 侧边栏：用户入口 ----------
render_auth_sidebar_entry()


# ---------- 3. 首页标题区 ----------
st.title("豆瓣读书数据可视化与 AI 阅读分析平台")

st.markdown("""
<div class="hero-box">
    <h3>基于图书数据的可视化分析与 AI 阅读推荐平台</h3>
    <p>
    本系统围绕豆瓣读书 Top250 数据，提供图书浏览、筛选检索、数据可视化、
    推荐关系分析与 AI 阅读推荐功能。用户可以在游客模式下浏览公共书库；
    登录后可维护个人书库，并在 AI 数据分析模块中分析公共书库、个人书库或混合数据。
    </p>
</div>
""", unsafe_allow_html=True)


# ---------- 4. 公共书库核心指标 ----------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("公共书库总数", len(public_df))

with col2:
    st.metric("平均评分", f"{public_df['评分'].mean():.2f}")

with col3:
    st.metric("最高评分", f"{public_df['评分'].max():.1f}")

with col4:
    st.metric("短评总赞", int(public_df["短评总赞"].sum()))


# ---------- 5. 侧边栏：公共书库筛选和分页 ----------
# 这里仅筛选公共书库，个人书库在“我的书库”和“AI 数据分析”中单独处理。
df_filtered, df_page, page, total_pages = render_book_sidebar(public_df)


# ---------- 6. 主功能区 ----------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "书籍总览",
    "数据可视化",
    "我的书库",
    "AI 推荐",
    "AI 数据分析"
])


with tab1:
    render_book_overview(
        df_page=df_page,
        page=page,
        total_pages=total_pages,
        api_ready=api_ready,
        client=client
    )


with tab2:
    render_book_charts(df_filtered)


with tab3:
    render_my_library(
        api_ready=api_ready,
        client=client
    )


with tab4:
    render_curator_chat(
        df_filtered=df_filtered,
        api_ready=api_ready,
        client=client
    )


with tab5:
    render_ai_data_analyst(
        public_df=public_df,
        api_ready=api_ready,
        client=client
    )
