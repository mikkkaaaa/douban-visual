import streamlit as st
import pandas as pd
import plotly.express as px

from io import StringIO

from components.user.auth import (
    get_current_user,
    is_logged_in,
    render_login_required_card
)

from lib.user_library_database import (
    init_user_library_table,
    insert_user_books,
    get_user_books,
    update_user_book,
    delete_user_book,
    clear_user_books
)

from utils.uploaded_data import read_uploaded_file, normalize_uploaded_books


def render_my_library(api_ready=None, client=None):
    """
    我的书库页面：
    1. 导入个人书籍数据
    2. 查看个人书库
    3. 修改书籍信息
    4. 基础可视化分析

    注意：
    AI 数据分析已经移动到 components/ai/data_analyst.py。
    这里不再放 AI 分析逻辑，避免功能重复。
    """
    if not is_logged_in():
        render_login_required_card("我的书库")
        return

    init_user_library_table()

    user = get_current_user()
    user_id = user["id"]
    username = user["username"]

    st.subheader("我的书库")
    st.caption(f"当前用户：{username}。这里保存的是你上传、粘贴或手动录入的个人书籍数据。")

    import_tab, library_tab, edit_tab, chart_tab = st.tabs([
        "导入数据",
        "书库列表",
        "修改书籍",
        "基础分析"
    ])

    with import_tab:
        render_import_area(user_id)

    with library_tab:
        render_library_table(user_id)

    with edit_tab:
        render_edit_book_area(user_id)

    with chart_tab:
        render_library_charts(user_id)


# =========================================================
# 导入数据
# =========================================================

def render_import_area(user_id):
    st.markdown("#### 导入个人书籍数据")

    st.info(
        "支持三种方式：上传 CSV / Excel、手动录入单本书、批量粘贴表格文本。"
        "推荐字段：书名、作者、评分、出版年份、评论数、简介、标签。"
    )

    upload_tab, manual_tab, paste_tab = st.tabs([
        "上传文件",
        "手动录入",
        "批量粘贴"
    ])

    with upload_tab:
        render_upload_area(user_id)

    with manual_tab:
        render_manual_input_area(user_id)

    with paste_tab:
        render_paste_table_area(user_id)


def render_upload_area(user_id):
    st.markdown("##### 上传 CSV / Excel 文件")

    uploaded_file = st.file_uploader(
        "选择 CSV 或 Excel 文件",
        type=["csv", "xlsx", "xls"]
    )

    if uploaded_file is None:
        st.caption("如果没有文件，可以切换到“手动录入”或“批量粘贴”。")
        return

    try:
        raw_df = read_uploaded_file(uploaded_file)
    except Exception as e:
        st.error(f"文件读取失败：{e}")
        return

    st.markdown("##### 原始数据预览")
    st.dataframe(raw_df.head(10), use_container_width=True)

    books_df = normalize_uploaded_books(raw_df)

    if books_df.empty:
        st.error("没有识别到有效书名，请检查表格中是否包含书名 / title / name 等字段。")
        return

    st.markdown("##### 系统识别后的数据")
    st.dataframe(books_df.head(20), use_container_width=True)

    col1, col2 = st.columns([1, 2])

    with col1:
        st.metric("可导入书籍数", len(books_df))

    with col2:
        st.caption("保存后，这些数据会写入 MySQL，并只归属于当前登录用户。")

    if st.button("保存到我的书库", use_container_width=True, key="save_uploaded_books"):
        try:
            inserted_count = insert_user_books(
                user_id=user_id,
                books_df=books_df,
                source_file=uploaded_file.name
            )

            st.success(f"成功导入 {inserted_count} 本书。")
            st.rerun()

        except Exception as e:
            st.error(f"保存失败：{e}")


def render_manual_input_area(user_id):
    st.markdown("##### 手动录入单本书")

    st.caption("适合用户没有 CSV 文件，只想把看到的图书信息手动保存进个人书库。")

    with st.form("manual_book_form", clear_on_submit=True):
        title = st.text_input(
            "书名 *",
            placeholder="例如：活着"
        )

        author = st.text_input(
            "作者",
            placeholder="例如：余华"
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            rating_text = st.text_input(
                "评分",
                placeholder="例如：9.4"
            )

        with col2:
            publish_year_text = st.text_input(
                "出版年份",
                placeholder="例如：1993"
            )

        with col3:
            comment_count_text = st.text_input(
                "评论数 / 热度",
                placeholder="例如：120000"
            )

        tags = st.text_input(
            "标签",
            placeholder="例如：小说, 现实主义, 中国文学"
        )

        intro = st.text_area(
            "简介",
            placeholder="可以输入这本书的简介、你看到的介绍，或者自己的备注。",
            height=120
        )

        submitted = st.form_submit_button(
            "保存这本书",
            use_container_width=True
        )

        if submitted:
            if not title.strip():
                st.error("书名不能为空。")
                return

            try:
                rating = parse_optional_float(rating_text)
                publish_year = parse_optional_int(publish_year_text)
                comment_count = parse_optional_int(comment_count_text)
            except ValueError as e:
                st.error(str(e))
                return

            book_df = pd.DataFrame([
                {
                    "书名": title.strip(),
                    "作者": author.strip(),
                    "评分": rating,
                    "出版年份": publish_year,
                    "评论数": comment_count,
                    "简介": intro.strip(),
                    "标签": tags.strip()
                }
            ])

            try:
                inserted_count = insert_user_books(
                    user_id=user_id,
                    books_df=book_df,
                    source_file="手动录入"
                )

                st.success(f"已保存 {inserted_count} 本书到你的个人书库。")
                st.rerun()

            except Exception as e:
                st.error(f"保存失败：{e}")


def render_paste_table_area(user_id):
    st.markdown("##### 批量粘贴表格文本")

    st.caption(
        "适合用户没有文件，但可以从网页、Excel、Notion 或其他地方复制表格内容。"
        "建议第一行包含字段名。"
    )

    with st.expander("查看粘贴格式示例"):
        st.code(
            """书名,作者,评分,出版年份,评论数,简介,标签
活着,余华,9.4,1993,120000,讲述人在苦难中的生存与承受,小说
百年孤独,加西亚·马尔克斯,9.3,1967,98000,布恩迪亚家族七代人的兴衰史,魔幻现实主义
局外人,阿尔贝·加缪,9.0,1942,76000,关于荒诞、冷漠与存在处境的小说,哲学小说"""
        )

    pasted_text = st.text_area(
        "粘贴表格内容",
        placeholder="把带表头的 CSV 或表格文本粘贴到这里",
        height=220
    )

    if not pasted_text.strip():
        return

    try:
        raw_df = read_pasted_table(pasted_text)
    except Exception as e:
        st.error(f"解析失败：{e}")
        st.caption("建议使用英文逗号分隔，或者从 Excel 复制带表头的表格。")
        return

    if raw_df.empty:
        st.error("没有解析到有效数据。")
        return

    st.markdown("##### 解析后的原始数据")
    st.dataframe(raw_df.head(20), use_container_width=True)

    books_df = normalize_uploaded_books(raw_df)

    if books_df.empty:
        st.error("没有识别到有效书名，请检查是否包含书名、标题、title 或 name 字段。")
        return

    st.markdown("##### 系统识别后的数据")
    st.dataframe(books_df.head(20), use_container_width=True)

    csv_preview = books_df.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        "下载识别结果 CSV",
        data=csv_preview,
        file_name="manual_books_preview.csv",
        mime="text/csv",
        use_container_width=True
    )

    if st.button("保存粘贴数据到我的书库", use_container_width=True, key="save_pasted_books"):
        try:
            inserted_count = insert_user_books(
                user_id=user_id,
                books_df=books_df,
                source_file="批量粘贴"
            )

            st.success(f"成功导入 {inserted_count} 本书。")
            st.rerun()

        except Exception as e:
            st.error(f"保存失败：{e}")


# =========================================================
# 书库列表
# =========================================================

def render_library_table(user_id):
    st.markdown("#### 我的书库列表")

    books = get_user_books(user_id)

    if books.empty:
        st.info("你的个人书库还没有数据。可以先在“导入数据”中上传、手动录入或批量粘贴。")
        return

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("书籍数量", len(books))

    with col2:
        if "评分" in books.columns:
            avg_rating = books["评分"].dropna().mean()
            st.metric(
                "平均评分",
                f"{avg_rating:.2f}" if not books["评分"].dropna().empty else "暂无"
            )

    with col3:
        if "出版年份" in books.columns:
            year_count = books["出版年份"].dropna().nunique()
            st.metric("年份跨度数", year_count)

    st.dataframe(
        books.drop(columns=["id"], errors="ignore"),
        use_container_width=True,
        height=420
    )

    csv = books.drop(columns=["id"], errors="ignore").to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        "下载我的书库 CSV",
        data=csv,
        file_name="my_library.csv",
        mime="text/csv",
        use_container_width=True
    )

    st.divider()

    with st.expander("删除 / 清空书库数据"):
        book_options = {
            f"{row['书名']}｜ID {row['id']}": row["id"]
            for _, row in books.iterrows()
        }

        selected_book_for_delete = st.selectbox(
            "选择要删除的书籍",
            list(book_options.keys()),
            key="delete_book_select"
        )

        delete_id = book_options[selected_book_for_delete]

        if st.button("删除选中书籍", use_container_width=True):
            deleted_count = delete_user_book(user_id, delete_id)

            if deleted_count > 0:
                st.success("已删除选中书籍。")
                st.rerun()
            else:
                st.warning("没有删除任何数据。")

        st.divider()

        confirm_clear = st.checkbox("我确认要清空我的个人书库")

        if confirm_clear:
            if st.button("清空我的书库", type="primary", use_container_width=True):
                cleared_count = clear_user_books(user_id)
                st.success(f"个人书库已清空，共删除 {cleared_count} 条数据。")
                st.rerun()


# =========================================================
# 修改书籍
# =========================================================

def render_edit_book_area(user_id):
    st.markdown("#### 修改书籍信息")

    books = get_user_books(user_id)

    if books.empty:
        st.info("你的个人书库还没有数据，暂时无法修改。请先导入或手动录入书籍。")
        return

    book_options = {
        f"{row['书名']}｜ID {row['id']}": row["id"]
        for _, row in books.iterrows()
    }

    selected_book = st.selectbox(
        "选择要修改的书籍",
        list(book_options.keys()),
        key="edit_book_select_main"
    )

    selected_id = book_options[selected_book]
    selected_row = get_selected_book_row(books, selected_id)

    if selected_row is None:
        st.warning("没有找到这本书的数据。")
        return

    st.caption("修改后点击保存，数据会更新到 MySQL 中的个人书库表。")

    with st.form("edit_book_form_main", clear_on_submit=False):
        title = st.text_input(
            "书名 *",
            value=value_to_text(selected_row.get("书名"))
        )

        author = st.text_input(
            "作者",
            value=value_to_text(selected_row.get("作者"))
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            rating_text = st.text_input(
                "评分",
                value=value_to_text(selected_row.get("评分")),
                placeholder="例如：9.4"
            )

        with col2:
            publish_year_text = st.text_input(
                "出版年份",
                value=value_to_text(selected_row.get("出版年份")),
                placeholder="例如：1993"
            )

        with col3:
            comment_count_text = st.text_input(
                "评论数 / 热度",
                value=value_to_text(selected_row.get("评论数")),
                placeholder="例如：120000"
            )

        tags = st.text_input(
            "标签",
            value=value_to_text(selected_row.get("标签")),
            placeholder="例如：小说, 哲学, 外国文学"
        )

        intro = st.text_area(
            "简介",
            value=value_to_text(selected_row.get("简介")),
            height=160
        )

        submitted = st.form_submit_button(
            "保存修改",
            use_container_width=True
        )

        if submitted:
            if not title.strip():
                st.error("书名不能为空。")
                return

            try:
                rating = parse_optional_float(rating_text)
                publish_year = parse_optional_int(publish_year_text)
                comment_count = parse_optional_int(comment_count_text)
            except ValueError as e:
                st.error(str(e))
                return

            book_data = {
                "书名": title.strip(),
                "作者": author.strip(),
                "评分": rating,
                "出版年份": publish_year,
                "评论数": comment_count,
                "简介": intro.strip(),
                "标签": tags.strip()
            }

            try:
                updated_count = update_user_book(
                    user_id=user_id,
                    book_id=selected_id,
                    book_data=book_data
                )

                if updated_count > 0:
                    st.success("书籍信息已更新。")
                    st.rerun()
                else:
                    st.warning("没有更新任何数据，请确认这本书是否仍在你的书库中。")

            except Exception as e:
                st.error(f"更新失败：{e}")


# =========================================================
# 基础分析
# =========================================================

def render_library_charts(user_id):
    st.markdown("#### 个人书库基础分析")

    books = get_user_books(user_id)

    if books.empty:
        st.info("暂无可分析的数据。请先导入个人书库。")
        return

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        if "评分" in books.columns and books["评分"].dropna().shape[0] > 0:
            fig = px.histogram(
                books,
                x="评分",
                nbins=10,
                title="个人书库评分分布"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("缺少评分字段，暂不能生成评分分布图。")

    with chart_col2:
        if "出版年份" in books.columns and books["出版年份"].dropna().shape[0] > 0:
            year_df = (
                books
                .dropna(subset=["出版年份"])
                .groupby("出版年份")
                .size()
                .reset_index(name="数量")
                .sort_values("出版年份")
            )

            fig = px.line(
                year_df,
                x="出版年份",
                y="数量",
                markers=True,
                title="个人书库出版年份分布"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("缺少出版年份字段，暂不能生成年份分布图。")

    st.divider()

    if "评分" in books.columns and books["评分"].dropna().shape[0] > 0:
        top_books = (
            books
            .dropna(subset=["评分"])
            .sort_values("评分", ascending=False)
            .head(10)
        )

        fig = px.bar(
            top_books,
            x="评分",
            y="书名",
            orientation="h",
            title="个人书库评分 Top10"
        )

        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)

    st.caption("当前分析基于用户上传、粘贴或手动录入的数据字段生成。")


# =========================================================
# 工具函数
# =========================================================

def read_pasted_table(text):
    text = text.strip()

    if not text:
        return pd.DataFrame()

    try:
        return pd.read_csv(
            StringIO(text),
            sep=None,
            engine="python"
        )
    except Exception:
        pass

    try:
        return pd.read_csv(
            StringIO(text),
            sep="\t"
        )
    except Exception:
        pass

    try:
        return pd.read_csv(
            StringIO(text),
            sep=","
        )
    except Exception:
        pass

    try:
        normalized_text = text.replace("，", ",")
        return pd.read_csv(
            StringIO(normalized_text),
            sep=","
        )
    except Exception:
        pass

    raise ValueError("无法识别表格格式")


def parse_optional_float(value):
    value = str(value).strip()

    if value == "":
        return None

    try:
        return float(value)
    except Exception:
        raise ValueError("评分必须是数字，例如 9.4。")


def parse_optional_int(value):
    value = str(value).strip()

    if value == "":
        return None

    try:
        return int(float(value))
    except Exception:
        raise ValueError("出版年份和评论数必须是整数，例如 1993 或 120000。")


def value_to_text(value):
    if pd.isna(value):
        return ""

    if isinstance(value, float) and value.is_integer():
        return str(int(value))

    return str(value)


def get_selected_book_row(books, selected_id):
    matched = books[books["id"] == selected_id]

    if matched.empty:
        return None

    return matched.iloc[0]