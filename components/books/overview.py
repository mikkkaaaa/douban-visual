import streamlit as st
import pandas as pd
from html import escape

from components.ai.prompts import build_book_summary_prompt

try:
    from utils.icon_loader import icon_title
except Exception:
    icon_title = None


def format_rating(rating):
    """
    统一格式化评分，避免 NaN 或 None 显示得很丑。
    """
    if rating is None or pd.isna(rating):
        return "暂无"

    try:
        return f"{float(rating):.1f}"
    except Exception:
        return str(rating)


def render_page_title():
    """
    渲染书籍总览模块标题。
    如果 SVG 图标工具不可用，就自动降级为普通标题。
    """
    if icon_title:
        icon_title(
            "assets/icons/book_open_text.svg",
            "书籍总览",
            "浏览当前筛选条件下的图书详情、相关推荐、热门短评与 AI 阅读指南。"
        )
    else:
        st.subheader("书籍总览")
        st.caption("浏览当前筛选条件下的图书详情、相关推荐、热门短评与 AI 阅读指南。")


def render_book_overview(df_page, page, total_pages, api_ready, client):
    render_page_title()

    if "book_summaries" not in st.session_state:
        st.session_state.book_summaries = {}

    if df_page.empty:
        st.info("当前筛选条件下没有书籍，请调整左侧筛选条件。")
        return

    st.caption(f"当前第 {page} 页 / 共 {total_pages} 页")

    for idx, row in df_page.iterrows():
        render_book_card(
            row=row,
            idx=idx,
            api_ready=api_ready,
            client=client
        )


def render_book_card(row, idx, api_ready, client):
    book_name = row.get("书名", "未知书名")
    rating = format_rating(row.get("评分", None))
    author_info = row.get("作者/出版信息", "暂无作者 / 出版信息")

    expander_title = f"{book_name}｜评分 {rating}"

    with st.expander(expander_title):
        st.markdown(f"### {book_name}")

        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"**作者 / 出版信息：** {author_info}")

            link = row.get("链接", "")
            if link and pd.notna(link):
                st.markdown(f"**豆瓣链接：** [点击打开]({link})")

        with col2:
            render_rating_badge(rating)

        st.divider()

        render_book_intro(row)

        st.divider()

        render_book_summary_button(
            row=row,
            idx=idx,
            api_ready=api_ready,
            client=client
        )

        render_recommendations(row)
        render_comments(row)


def render_rating_badge(rating):
    """
    渲染评分徽章，替代原来的星星评分。
    """
    st.markdown(
        f"""
        <div class="rating-badge">
            <span class="rating-number">{rating}</span>
            <span class="rating-label">豆瓣评分</span>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_book_intro(row):
    st.markdown("#### 内容信息")

    short_intro = row.get("短简介", "")

    if short_intro and pd.notna(short_intro):
        st.markdown(f"**短简介：** {short_intro}")
    else:
        st.caption("暂无短简介。")

    long_intro = row.get("长简介", "")

    if long_intro and pd.notna(long_intro):
        with st.expander("查看详细介绍"):
            st.markdown(str(long_intro))

    author_intro = row.get("作者简介", "")

    if author_intro and pd.notna(author_intro):
        with st.expander("查看作者简介"):
            st.markdown(str(author_intro))


def render_book_summary_button(row, idx, api_ready, client):
    book_name = row.get("书名", "未知书名")

    st.markdown("#### AI 阅读指南")

    if not api_ready:
        st.caption("AI 阅读指南暂不可用，请检查 API Key 配置。")
        return

    if book_name not in st.session_state.book_summaries:
        if st.button(
            f"生成《{book_name}》阅读指南",
            key=f"summary_{idx}_{book_name}",
            use_container_width=True
        ):
            with st.spinner(f"正在生成《{book_name}》阅读指南..."):
                prompt = build_book_summary_prompt(row)

                try:
                    resp = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        temperature=0.6
                    )

                    st.session_state.book_summaries[book_name] = resp.choices[0].message.content
                    st.rerun()

                except Exception as e:
                    st.error(f"生成失败：{e}")

    if book_name in st.session_state.book_summaries:
        st.success(f"《{book_name}》阅读指南已生成")
        st.markdown(st.session_state.book_summaries[book_name])


def render_recommendations(row):
    recs = row.get("相关推荐_list", [])

    if not recs:
        return

    st.divider()
    st.markdown("#### 相关推荐")

    for rec in recs:
        if not isinstance(rec, dict):
            continue

        title = rec.get("title", "未知书籍")
        link = rec.get("link", "#")
        rate = rec.get("rate", "暂无评分")

        st.markdown(f"- [{title}]({link}) ｜ 评分：{rate}")


def render_comments(row):
    comments = row.get("短评_list", [])

    if not comments:
        return

    st.divider()
    st.markdown("#### 热门短评")

    for comment in comments:
        if not isinstance(comment, dict):
            continue

        text = comment.get("comment", "")
        vote = comment.get("vote", 0)

        if not text:
            continue

        safe_text = escape(str(text))
        safe_vote = escape(str(vote))

        st.markdown(
            f"""
            <div class="comment-card">
                <p>{safe_text}</p>
                <span>赞同：{safe_vote}</span>
            </div>
            """,
            unsafe_allow_html=True
        )