import streamlit as st
import pandas as pd


def render_book_sidebar(df):
    """
    侧边栏组件：
    1. 图书筛选
    2. 排序方式
    3. 当前结果统计
    4. CSV 数据导出
    5. 分页控制
    """

    with st.sidebar:
        # ---------- 1. 筛选条件 ----------
        st.markdown("### 筛选与搜索")
        st.caption("根据评分范围、书名或作者信息筛选图书。")

        min_rating, max_rating = st.slider(
            "评分范围",
            min_value=0.0,
            max_value=10.0,
            value=(8.5, 10.0),
            step=0.1
        )

        search_keyword = st.text_input(
            "搜索书名或作者",
            placeholder="例如：活着、鲁迅、村上春树"
        )

        sort_option = st.selectbox(
            "排序方式",
            [
                "评分从高到低",
                "短评热度从高到低",
                "出版年份从新到旧",
                "出版年份从旧到新"
            ]
        )

    # ---------- 2. 数据筛选 ----------
    df_filtered = df.copy()

    df_filtered = df_filtered[
        (df_filtered["评分"] >= min_rating) &
        (df_filtered["评分"] <= max_rating)
    ]

    if search_keyword.strip():
        keyword = search_keyword.strip()

        df_filtered = df_filtered[
            df_filtered["书名"].fillna("").str.contains(keyword, case=False, na=False) |
            df_filtered["作者/出版信息"].fillna("").str.contains(keyword, case=False, na=False)
        ]

    # ---------- 3. 排序 ----------
    if sort_option == "评分从高到低":
        df_filtered = df_filtered.sort_values("评分", ascending=False)

    elif sort_option == "短评热度从高到低" and "短评总赞" in df_filtered.columns:
        df_filtered = df_filtered.sort_values("短评总赞", ascending=False)

    elif sort_option == "出版年份从新到旧" and "出版年份" in df_filtered.columns:
        df_filtered = df_filtered.sort_values("出版年份", ascending=False)

    elif sort_option == "出版年份从旧到新" and "出版年份" in df_filtered.columns:
        df_filtered = df_filtered.sort_values("出版年份", ascending=True)

    # ---------- 4. 当前结果与导出 ----------
    with st.sidebar:
        st.divider()
        st.markdown("### 当前结果")

        st.metric(
            label="符合条件的图书",
            value=f"{len(df_filtered)} 本"
        )

        st.divider()
        st.markdown("### 数据导出")
        st.caption("导出当前筛选和排序后的图书数据。")

        if len(df_filtered) > 0:
            export_cols = [
                "书名",
                "评分",
                "作者/出版信息",
                "出版年份",
                "短评总赞",
                "短简介",
                "链接"
            ]

            export_df = df_filtered[
                [col for col in export_cols if col in df_filtered.columns]
            ].copy()

            csv = export_df.to_csv(index=False).encode("utf-8-sig")

            st.download_button(
                label="下载当前结果 CSV",
                data=csv,
                file_name="books_filtered.csv",
                mime="text/csv",
                key="download_filtered_books",
                use_container_width=True
            )
        else:
            st.info("暂无可导出的数据")

        # ---------- 5. 分页 ----------
        st.divider()
        st.markdown("### 分页设置")

        books_per_page = st.selectbox(
            "每页显示数量",
            [10, 20, 30, 50],
            index=1
        )

    if len(df_filtered) > 0:
        total_pages = max(1, (len(df_filtered) - 1) // books_per_page + 1)

        with st.sidebar:
            page = st.number_input(
                "选择页码",
                min_value=1,
                max_value=total_pages,
                value=1
            )

            st.caption(f"共 {total_pages} 页")

        start_idx = (page - 1) * books_per_page
        end_idx = start_idx + books_per_page

        df_page = df_filtered.iloc[start_idx:end_idx]

    else:
        page = 1
        total_pages = 1
        df_page = pd.DataFrame()

        with st.sidebar:
            st.warning("没有找到匹配的图书")

    return df_filtered, df_page, page, total_pages