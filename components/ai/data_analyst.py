import json
import re

import pandas as pd
import streamlit as st
import plotly.express as px

from components.user.auth import is_logged_in, get_current_user
from lib.user_library_database import get_user_books

from utils.data_unifier import (
    normalize_public_books,
    normalize_user_books,
    combine_books
)


# =========================================================
# 主入口
# =========================================================

def render_ai_data_analyst(public_df, api_ready, client):
    """
    AI 数据分析模块。

    功能：
    1. 选择分析数据源：公共书库 / 我的书库 / 公共书库 + 我的书库
    2. 生成 AI 数据分析报告
    3. AI 自动生成图表 Dashboard
    4. AI 自定义生成单个图表

    注意：
    这里的数据统一只用于 AI 分析，不影响原来的书籍总览和数据可视化页面。
    """

    st.subheader("AI 数据分析")

    st.markdown("""
    这个模块用于对不同来源的图书数据进行智能分析。  
    公共书库来自豆瓣读书 Top250 爬虫数据；个人书库来自用户上传、粘贴或手动录入的数据。
    """)

    if not api_ready or client is None:
        st.error("AI 数据分析暂不可用，请检查 DeepSeek API Key 配置。")
        return

    source_options = ["公共书库"]

    if is_logged_in():
        source_options.extend([
            "我的书库",
            "公共书库 + 我的书库"
        ])
    else:
        st.info("当前是游客模式，只能分析公共书库。登录后可以分析个人书库和混合数据。")

    source_name = st.radio(
        "选择分析数据源",
        source_options,
        horizontal=True,
        key="ai_data_source_selector"
    )

    analysis_df = get_analysis_dataframe(
        public_df=public_df,
        source_name=source_name
    )

    if analysis_df.empty:
        st.warning("当前数据源暂无可分析数据。")
        return

    render_data_overview(analysis_df, source_name)

    st.divider()

    render_ai_analysis_controls(
        df=analysis_df,
        source_name=source_name,
        client=client
    )

    st.divider()

    render_ai_chart_dashboard(
        df=analysis_df,
        source_name=source_name,
        client=client
    )

    st.divider()

    render_ai_single_chart_generator(
        df=analysis_df,
        source_name=source_name,
        client=client
    )


def get_analysis_dataframe(public_df, source_name):
    """
    根据用户选择生成 AI 分析用 DataFrame。
    """

    if source_name == "公共书库":
        return normalize_public_books(public_df)

    if not is_logged_in():
        return normalize_public_books(public_df)

    user = get_current_user()
    user_books_raw = get_user_books(user["id"])

    if source_name == "我的书库":
        return normalize_user_books(user_books_raw)

    if source_name == "公共书库 + 我的书库":
        return combine_books(public_df, user_books_raw)

    return normalize_public_books(public_df)


# =========================================================
# 数据概览
# =========================================================

def render_data_overview(df, source_name):
    """
    展示当前 AI 分析数据源的基础概况。
    """

    st.markdown(f"#### 当前数据源：{source_name}")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("书籍数量", len(df))

    with col2:
        rating_series = get_numeric_series(df, "评分")

        if not rating_series.empty:
            st.metric("平均评分", f"{rating_series.mean():.2f}")
        else:
            st.metric("平均评分", "暂无")

    with col3:
        year_series = get_numeric_series(df, "出版年份")

        if not year_series.empty:
            year_min = int(year_series.min())
            year_max = int(year_series.max())
            st.metric("年份范围", f"{year_min} - {year_max}")
        else:
            st.metric("年份范围", "暂无")

    with col4:
        if "来源" in df.columns:
            st.metric("数据来源数", df["来源"].nunique())
        else:
            st.metric("数据来源数", 1)

    with st.expander("查看当前分析数据预览"):
        preview_cols = [
            "书名",
            "评分",
            "作者/出版信息",
            "出版年份",
            "短评总赞",
            "标签",
            "来源"
        ]

        preview_df = df[
            [col for col in preview_cols if col in df.columns]
        ].copy()

        st.dataframe(
            preview_df.head(80),
            use_container_width=True,
            height=360
        )


# =========================================================
# AI 数据分析报告
# =========================================================

def render_ai_analysis_controls(df, source_name, client):
    """
    AI 分析报告控制区。
    """

    st.markdown("#### 生成 AI 数据分析报告")

    suffix = make_key_suffix(source_name)

    analysis_focus = st.selectbox(
        "分析重点",
        [
            "综合分析",
            "评分与热度分析",
            "出版年份与时间分布分析",
            "阅读偏好与标签分析",
            "适合做哪些可视化图表"
        ],
        key=f"analysis_focus_{suffix}"
    )

    report_length = st.radio(
        "报告长度",
        [
            "简洁版",
            "详细版"
        ],
        horizontal=True,
        key=f"report_length_{suffix}"
    )

    report_key = f"ai_data_analysis_report_{suffix}"

    if st.button(
        "生成 AI 分析报告",
        use_container_width=True,
        key=f"generate_report_{suffix}"
    ):
        prompt = build_ai_data_analysis_prompt(
            df=df,
            source_name=source_name,
            analysis_focus=analysis_focus,
            report_length=report_length
        )

        with st.spinner("正在生成数据分析报告..."):
            try:
                resp = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.4
                )

                result = resp.choices[0].message.content

                st.session_state[report_key] = result

            except Exception as e:
                st.error(f"AI 分析失败：{e}")
                return

    if report_key in st.session_state:
        st.markdown("#### AI 分析结果")
        st.markdown(st.session_state[report_key])


def build_ai_data_analysis_prompt(df, source_name, analysis_focus, report_length):
    """
    构造 AI 数据分析 Prompt。
    """

    data_summary = build_dataset_summary(df)
    sample_text = build_sample_books_text(df)
    column_summary = build_column_summary(df)

    return f"""
你是一名数据分析助理，正在分析一个图书数据集。

数据源：{source_name}
分析重点：{analysis_focus}
报告长度：{report_length}

请根据下面的数据概况、字段信息和样本数据，生成一份清楚、自然、克制的数据分析报告。

要求：
1. 只根据提供的数据分析，不要编造没有给出的信息。
2. 不要写成营销文案，也不要使用过度抒情的表达。
3. 如果某些字段缺失或数据不足，请直接说明。
4. 分析要具体，尽量结合评分、热度、出版年份、标签、来源等字段。
5. 最后给出 2-4 个适合当前数据的可视化图表建议。
6. 图表建议只需要说明图表类型、使用字段和分析目的，不要写代码。

请按下面结构输出：

### 1. 数据概况
说明当前数据源包含多少本书、主要字段完整度如何。

### 2. 主要数据特征
结合评分、热度、年份、标签或来源字段，说明你观察到的特征。

### 3. 可视化分析建议
列出 2-4 个适合生成的图表，例如柱状图、折线图、散点图、饼图等，并说明每个图表适合观察什么。

### 4. 数据不足与改进方向
说明如果想让分析更准确，还可以补充哪些字段或数据。

【字段信息】
{column_summary}

【数据概况】
{data_summary}

【样本书籍】
{sample_text}
"""


# =========================================================
# AI 图表 Dashboard
# =========================================================

def render_ai_chart_dashboard(df, source_name, client):
    """
    AI 自动生成图表 Dashboard。
    一次生成 3 个图表方案，并用 Plotly 绘制。
    """

    st.markdown("#### AI 自动生成图表 Dashboard")

    st.caption(
        "点击按钮后，AI 会根据当前数据源自动设计 3 个适合展示的图表，"
        "系统会校验字段并用 Plotly 自动绘制。"
    )

    suffix = make_key_suffix(source_name)
    dashboard_key = f"ai_chart_dashboard_{suffix}"
    dashboard_summary_key = f"ai_chart_dashboard_summary_{suffix}"

    col1, col2 = st.columns([2, 1])

    with col1:
        dashboard_goal = st.text_input(
            "Dashboard 目标",
            placeholder="例如：帮我做一个适合毕设展示的图书数据分析图表组合",
            key=f"dashboard_goal_{suffix}"
        )

    with col2:
        chart_count = st.selectbox(
            "图表数量",
            [3, 4],
            index=0,
            key=f"dashboard_chart_count_{suffix}"
        )

    if st.button(
        "一键生成 AI 图表 Dashboard",
        use_container_width=True,
        key=f"generate_dashboard_{suffix}"
    ):
        if not dashboard_goal.strip():
            dashboard_goal = "请根据当前数据生成一个适合毕业设计展示的图书数据分析图表组合。"

        prompt = build_ai_dashboard_plan_prompt(
            df=df,
            source_name=source_name,
            dashboard_goal=dashboard_goal,
            chart_count=chart_count
        )

        with st.spinner("AI 正在生成图表 Dashboard..."):
            try:
                resp = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.15
                )

                raw_result = resp.choices[0].message.content

                dashboard_result = parse_ai_dashboard_json(raw_result)

                chart_plans = dashboard_result.get("charts", [])
                dashboard_summary = dashboard_result.get("dashboard_summary", "")

                valid_plans = []

                for plan in chart_plans:
                    normalized_plan = normalize_chart_plan(plan)
                    ok, message = validate_chart_plan(normalized_plan, df)

                    if ok:
                        valid_plans.append(normalized_plan)

                if not valid_plans:
                    st.warning("AI 返回的图表方案不可用，系统将使用默认图表方案。")
                    valid_plans = build_default_dashboard_plans(df)

                st.session_state[dashboard_key] = valid_plans
                st.session_state[dashboard_summary_key] = dashboard_summary

            except Exception as e:
                st.warning(f"AI Dashboard 生成失败，系统将使用默认图表方案。错误：{e}")
                st.session_state[dashboard_key] = build_default_dashboard_plans(df)
                st.session_state[dashboard_summary_key] = "系统根据当前字段自动生成了默认图表组合。"

    if dashboard_key in st.session_state:
        chart_plans = st.session_state[dashboard_key]
        dashboard_summary = st.session_state.get(dashboard_summary_key, "")

        if dashboard_summary:
            st.info(dashboard_summary)

        render_chart_plan_grid(df, chart_plans, section_key=dashboard_key)


def build_ai_dashboard_plan_prompt(df, source_name, dashboard_goal, chart_count=3):
    """
    让 AI 一次返回多个图表方案。
    """

    columns = list(df.columns)
    numeric_columns = get_numeric_columns(df)
    column_summary = build_column_summary(df)
    dataset_summary = build_dataset_summary(df)

    return f"""
你是一名数据可视化分析师。你需要为一个图书数据集生成一个 Dashboard 图表组合方案。

重要限制：
1. 只能返回 JSON，不要返回解释文字，不要使用 Markdown 代码块。
2. 不要生成 Python 代码。
3. 必须返回 {chart_count} 个图表方案。
4. chart_type 只能是：bar、line、scatter、pie。
5. x、y、size 字段必须从可用字段中选择。
6. 如果是统计数量，可以让 aggregate 使用 count，此时 y 可以为空字符串。
7. 如果字段数据不足，请选择更稳妥的图表。
8. scatter 必须同时有 x 和 y，并且二者应该是数值字段。
9. pie 适合展示少量分类占比，例如来源分布、标签分布。
10. 如果使用 标签 字段做分类统计，可以设置 explode_tags 为 true。
11. 不要所有图表都用同一种类型，尽量组合出能展示不同角度的图表。
12. 如果当前数据只有公共书库，推荐包含：评分 Top10、出版年份趋势、评分与热度关系。
13. 如果当前数据包含混合来源，推荐包含：来源分布、评分 Top10、出版年份趋势或标签分布。

当前数据源：{source_name}

Dashboard 目标：
{dashboard_goal}

可用字段：
{columns}

数值字段：
{numeric_columns}

字段完整度：
{column_summary}

数据概况：
{dataset_summary}

请严格返回以下 JSON 格式：

{{
  "dashboard_summary": "用一句话说明这个 Dashboard 主要展示什么",
  "charts": [
    {{
      "chart_type": "bar",
      "title": "图表标题",
      "description": "这张图展示什么",
      "x": "字段名",
      "y": "字段名或空字符串",
      "size": "字段名或空字符串",
      "aggregate": "count",
      "top_n": 10,
      "sort": "desc",
      "explode_tags": false,
      "reason": "为什么选择这张图"
    }}
  ]
}}

字段说明：
- chart_type：bar / line / scatter / pie
- x：横轴字段或分类字段
- y：数值字段；如果 aggregate 是 count，可以为空字符串
- size：只在 scatter 中可选，用于气泡大小；不用则为空字符串
- aggregate：none / count / mean / sum
- top_n：最多展示多少条，建议 10
- sort：desc / asc / none
- explode_tags：只有 x 是 标签 时才建议使用 true
"""


def parse_ai_dashboard_json(raw_text):
    """
    解析 AI Dashboard JSON。
    """

    text = clean_json_text(raw_text)

    try:
        data = json.loads(text)
    except Exception:
        match = re.search(r"\{[\s\S]*\}", text)

        if not match:
            raise ValueError("没有识别到 Dashboard JSON。")

        data = json.loads(match.group(0))

    if isinstance(data, list):
        return {
            "dashboard_summary": "",
            "charts": data
        }

    if "charts" not in data:
        return {
            "dashboard_summary": data.get("dashboard_summary", ""),
            "charts": [data]
        }

    return data


def build_default_dashboard_plans(df):
    """
    当 AI 返回失败时，使用默认图表方案。
    """

    plans = []

    if "评分" in df.columns and "书名" in df.columns:
        plans.append({
            "chart_type": "bar",
            "title": "评分最高的图书 Top10",
            "description": "展示当前数据源中评分最高的图书。",
            "x": "书名",
            "y": "评分",
            "size": "",
            "aggregate": "none",
            "top_n": 10,
            "sort": "desc",
            "explode_tags": False,
            "reason": "用于快速识别当前数据中评分最高的图书。"
        })

    if "出版年份" in df.columns:
        plans.append({
            "chart_type": "line",
            "title": "出版年份分布趋势",
            "description": "展示不同出版年份的图书数量变化。",
            "x": "出版年份",
            "y": "",
            "size": "",
            "aggregate": "count",
            "top_n": 30,
            "sort": "asc",
            "explode_tags": False,
            "reason": "用于观察图书出版年份的时间分布。"
        })

    if "评分" in df.columns and "短评总赞" in df.columns:
        plans.append({
            "chart_type": "scatter",
            "title": "评分与热度关系",
            "description": "观察评分和热度之间是否存在关系。",
            "x": "短评总赞",
            "y": "评分",
            "size": "短评总赞",
            "aggregate": "none",
            "top_n": 30,
            "sort": "none",
            "explode_tags": False,
            "reason": "用于观察高评分图书是否也具有较高讨论热度。"
        })

    if "来源" in df.columns and df["来源"].nunique() > 1:
        plans.insert(0, {
            "chart_type": "pie",
            "title": "不同来源书籍占比",
            "description": "展示公共书库和个人书库的数据占比。",
            "x": "来源",
            "y": "",
            "size": "",
            "aggregate": "count",
            "top_n": 10,
            "sort": "desc",
            "explode_tags": False,
            "reason": "用于观察当前数据源中不同来源图书的构成。"
        })

    if "标签" in df.columns:
        plans.append({
            "chart_type": "bar",
            "title": "高频标签 Top10",
            "description": "展示当前数据中出现频率最高的标签。",
            "x": "标签",
            "y": "",
            "size": "",
            "aggregate": "count",
            "top_n": 10,
            "sort": "desc",
            "explode_tags": True,
            "reason": "用于观察当前图书数据的主题和类型分布。"
        })

    return plans[:3]


def render_chart_plan_grid(df, chart_plans, section_key):
    """
    渲染多个图表。
    """

    for index, plan in enumerate(chart_plans):
        st.markdown(f"##### {index + 1}. {plan.get('title', 'AI 图表')}")

        try:
            fig, chart_df = build_plotly_chart_from_plan(df, plan)

            st.plotly_chart(
                fig,
                use_container_width=True,
                key=f"{section_key}_chart_{index}"
            )

            if plan.get("reason"):
                st.caption(plan.get("reason"))

            with st.expander(f"查看图表 {index + 1} 的数据和方案"):
                st.markdown("###### 图表数据")
                st.dataframe(chart_df, use_container_width=True)

                st.markdown("###### 图表方案")
                st.json(plan)

        except Exception as e:
            st.error(f"图表 {index + 1} 绘制失败：{e}")


# =========================================================
# AI 自定义单图生成
# =========================================================

def render_ai_single_chart_generator(df, source_name, client):
    """
    用户用自然语言自定义生成一个图表。
    """

    st.markdown("#### 自定义 AI 图表")

    st.caption(
        "这里适合临时提问，例如：生成评分最高的书籍 Top10、看评分和热度关系、统计标签分布。"
    )

    suffix = make_key_suffix(source_name)

    user_request = st.text_input(
        "你想生成什么图？",
        placeholder="例如：帮我生成评分最高的书籍 Top10 / 看评分和热度的关系 / 统计标签分布",
        key=f"ai_single_chart_request_{suffix}"
    )

    chart_key = f"ai_single_chart_plan_{suffix}"

    if st.button(
        "生成自定义 AI 图表",
        use_container_width=True,
        key=f"generate_single_chart_{suffix}"
    ):
        if not user_request.strip():
            user_request = "请根据当前数据选择一个最适合展示数据特征的图表。"

        prompt = build_ai_single_chart_plan_prompt(
            df=df,
            source_name=source_name,
            user_request=user_request
        )

        with st.spinner("AI 正在生成图表方案..."):
            try:
                resp = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.1
                )

                raw_result = resp.choices[0].message.content

                chart_plan = parse_ai_chart_json(raw_result)
                chart_plan = normalize_chart_plan(chart_plan)

                ok, message = validate_chart_plan(chart_plan, df)

                if not ok:
                    st.error(f"AI 生成的图表方案不可用：{message}")

                    with st.expander("查看 AI 原始返回内容"):
                        st.code(raw_result)

                    return

                st.session_state[chart_key] = chart_plan

            except Exception as e:
                st.error(f"AI 图表生成失败：{e}")
                return

    if chart_key in st.session_state:
        chart_plan = st.session_state[chart_key]

        try:
            fig, chart_df = build_plotly_chart_from_plan(df, chart_plan)

            st.plotly_chart(fig, use_container_width=True)

            if chart_plan.get("reason"):
                st.caption(chart_plan.get("reason"))

            with st.expander("查看图表数据和 AI 图表方案"):
                st.markdown("##### 图表数据")
                st.dataframe(chart_df, use_container_width=True)

                st.markdown("##### AI 图表方案 JSON")
                st.json(chart_plan)

        except Exception as e:
            st.error(f"图表绘制失败：{e}")
            st.caption("可以换一种描述方式重新生成，例如：生成评分 Top10 柱状图。")


def build_ai_single_chart_plan_prompt(df, source_name, user_request):
    """
    让 AI 返回单个图表方案。
    """

    columns = list(df.columns)
    numeric_columns = get_numeric_columns(df)
    column_summary = build_column_summary(df)
    dataset_summary = build_dataset_summary(df)

    return f"""
你是一名数据可视化助手。你需要根据用户需求和当前图书数据字段，生成一个图表方案 JSON。

重要限制：
1. 只能返回 JSON，不要返回解释文字，不要使用 Markdown 代码块。
2. 不要生成 Python 代码。
3. chart_type 只能是以下四种之一：bar、line、scatter、pie。
4. x、y、size 字段必须从可用字段中选择。
5. 如果是统计数量，可以让 aggregate 使用 count，此时 y 可以为空字符串。
6. 如果字段数据不足，请选择更稳妥的图表。
7. 图书名称较多时，优先使用 bar，并设置 top_n 为 10。
8. scatter 必须同时有 x 和 y，并且二者最好是数值字段。
9. pie 适合展示少量分类占比，例如来源分布、标签分布。
10. 如果用户要求“评分最高的书”，优先使用：
    chart_type = bar
    x = 书名
    y = 评分
    aggregate = none
    sort = desc
    top_n = 10
11. 如果用户要求“出版年份趋势”，优先使用：
    chart_type = line
    x = 出版年份
    y = 空字符串
    aggregate = count
    sort = asc
12. 如果用户要求“标签分布”，优先使用：
    chart_type = bar
    x = 标签
    y = 空字符串
    aggregate = count
    explode_tags = true
    sort = desc

当前数据源：{source_name}

用户需求：
{user_request}

可用字段：
{columns}

数值字段：
{numeric_columns}

字段完整度：
{column_summary}

数据概况：
{dataset_summary}

请严格返回以下 JSON 格式：

{{
  "chart_type": "bar",
  "title": "图表标题",
  "description": "这张图展示什么",
  "x": "字段名",
  "y": "字段名或空字符串",
  "size": "字段名或空字符串",
  "aggregate": "count",
  "top_n": 10,
  "sort": "desc",
  "explode_tags": false,
  "reason": "为什么选择这张图"
}}
"""


def parse_ai_chart_json(raw_text):
    """
    解析单个图表 JSON。
    """

    text = clean_json_text(raw_text)

    try:
        data = json.loads(text)
    except Exception:
        match = re.search(r"\{[\s\S]*\}", text)

        if not match:
            raise ValueError("没有识别到 JSON。")

        data = json.loads(match.group(0))

    if "charts" in data and isinstance(data["charts"], list) and data["charts"]:
        return data["charts"][0]

    return data


# =========================================================
# 图表方案校验与绘制
# =========================================================

def normalize_chart_plan(plan):
    """
    兼容不同字段名，统一成系统内部使用的字段。
    """

    alias_map = {
        "type": "chart_type",
        "chart": "chart_type",
        "chartType": "chart_type",
        "x_field": "x",
        "y_field": "y",
        "size_field": "size",
        "agg": "aggregate",
        "limit": "top_n",
        "explodeTag": "explode_tags",
        "explode_tags": "explode_tags"
    }

    normalized = {}

    for key, value in plan.items():
        new_key = alias_map.get(key, key)
        normalized[new_key] = value

    normalized["chart_type"] = str(normalized.get("chart_type", "bar")).strip().lower()
    normalized["title"] = str(normalized.get("title", "AI 生成图表")).strip()
    normalized["description"] = str(normalized.get("description", "")).strip()
    normalized["x"] = normalize_field_name(normalized.get("x", ""))
    normalized["y"] = normalize_field_name(normalized.get("y", ""))
    normalized["size"] = normalize_field_name(normalized.get("size", ""))
    normalized["aggregate"] = str(normalized.get("aggregate", "count")).strip().lower()
    normalized["sort"] = str(normalized.get("sort", "desc")).strip().lower()
    normalized["reason"] = str(normalized.get("reason", "")).strip()

    explode_tags_value = normalized.get("explode_tags", False)

    if isinstance(explode_tags_value, str):
        normalized["explode_tags"] = explode_tags_value.strip().lower() in ["true", "1", "yes", "是"]
    else:
        normalized["explode_tags"] = bool(explode_tags_value)

    try:
        normalized["top_n"] = int(normalized.get("top_n", 10))
    except Exception:
        normalized["top_n"] = 10

    normalized["top_n"] = max(3, min(normalized["top_n"], 30))

    return normalized


def normalize_field_name(value):
    """
    处理 AI 可能返回的空字段。
    """

    if value is None:
        return ""

    text = str(value).strip()

    empty_values = [
        "",
        "无",
        "空",
        "空字符串",
        "none",
        "None",
        "null",
        "Null",
        "N/A",
        "不使用"
    ]

    if text in empty_values:
        return ""

    return text


def validate_chart_plan(plan, df):
    """
    校验 AI 返回的图表方案是否能执行。
    """

    allowed_chart_types = ["bar", "line", "scatter", "pie"]
    allowed_aggregates = ["none", "count", "mean", "sum"]
    allowed_sorts = ["desc", "asc", "none"]

    chart_type = plan.get("chart_type")
    x = plan.get("x")
    y = plan.get("y")
    size = plan.get("size")
    aggregate = plan.get("aggregate")
    sort = plan.get("sort")

    if chart_type not in allowed_chart_types:
        return False, f"不支持的图表类型：{chart_type}"

    if aggregate not in allowed_aggregates:
        return False, f"不支持的聚合方式：{aggregate}"

    if sort not in allowed_sorts:
        return False, f"不支持的排序方式：{sort}"

    if not x:
        return False, "缺少 x 字段。"

    if x not in df.columns:
        return False, f"x 字段不存在：{x}"

    if chart_type == "scatter":
        if not y:
            return False, "散点图必须提供 y 字段。"

        if y not in df.columns:
            return False, f"y 字段不存在：{y}"

    if y and y not in df.columns:
        return False, f"y 字段不存在：{y}"

    if size and size not in df.columns:
        return False, f"size 字段不存在：{size}"

    if aggregate in ["mean", "sum"] and not y:
        return False, f"{aggregate} 聚合方式必须提供 y 字段。"

    if aggregate == "none" and chart_type in ["bar", "line"] and not y:
        return False, "未聚合图表必须提供 y 字段。"

    return True, "ok"


def build_plotly_chart_from_plan(df, plan):
    """
    根据图表方案生成 Plotly 图表。
    """

    chart_type = plan.get("chart_type", "bar")
    title = plan.get("title", "AI 生成图表")
    x = plan.get("x")
    y = plan.get("y")
    size = plan.get("size")
    aggregate = plan.get("aggregate", "count")
    top_n = plan.get("top_n", 10)
    sort = plan.get("sort", "desc")
    explode_tags = plan.get("explode_tags", False)

    chart_df = df.copy()

    if chart_type == "bar":
        final_df, value_col = prepare_aggregated_chart_data(
            chart_df=chart_df,
            x=x,
            y=y,
            aggregate=aggregate,
            top_n=top_n,
            sort=sort,
            explode_tags=explode_tags
        )

        if len(final_df) > 6:
            fig = px.bar(
                final_df,
                x=value_col,
                y=x,
                orientation="h",
                title=title,
                hover_data=final_df.columns
            )

            fig.update_layout(yaxis={"categoryorder": "total ascending"})
        else:
            fig = px.bar(
                final_df,
                x=x,
                y=value_col,
                title=title,
                hover_data=final_df.columns
            )

        return fig, final_df

    if chart_type == "line":
        final_df, value_col = prepare_aggregated_chart_data(
            chart_df=chart_df,
            x=x,
            y=y,
            aggregate=aggregate,
            top_n=None,
            sort="none",
            explode_tags=explode_tags
        )

        final_df = sort_by_dimension(final_df, x)

        fig = px.line(
            final_df,
            x=x,
            y=value_col,
            markers=True,
            title=title,
            hover_data=final_df.columns
        )

        return fig, final_df

    if chart_type == "pie":
        final_df, value_col = prepare_aggregated_chart_data(
            chart_df=chart_df,
            x=x,
            y=y,
            aggregate=aggregate if aggregate != "none" else "count",
            top_n=top_n,
            sort=sort,
            explode_tags=explode_tags
        )

        fig = px.pie(
            final_df,
            names=x,
            values=value_col,
            title=title
        )

        return fig, final_df

    if chart_type == "scatter":
        final_df = prepare_scatter_chart_data(
            chart_df=chart_df,
            x=x,
            y=y,
            size=size
        )

        hover_name = "书名" if "书名" in final_df.columns else None

        hover_cols = [
            col
            for col in ["作者/出版信息", "出版年份", "来源", "标签"]
            if col in final_df.columns
        ]

        if size and size in final_df.columns and final_df[size].sum() > 0:
            fig = px.scatter(
                final_df,
                x=x,
                y=y,
                size=size,
                hover_name=hover_name,
                hover_data=hover_cols,
                size_max=45,
                title=title
            )
        else:
            fig = px.scatter(
                final_df,
                x=x,
                y=y,
                hover_name=hover_name,
                hover_data=hover_cols,
                title=title
            )

        return fig, final_df

    raise ValueError(f"暂不支持的图表类型：{chart_type}")


def prepare_aggregated_chart_data(chart_df, x, y, aggregate, top_n=10, sort="desc", explode_tags=False):
    """
    处理柱状图、折线图、饼图的数据聚合。
    """

    df = chart_df.copy()

    if x not in df.columns:
        raise ValueError(f"字段不存在：{x}")

    if explode_tags and x == "标签":
        df = explode_tags_dataframe(df, tag_col="标签")
        x = "标签"

    df[x] = clean_dimension_series(df[x])
    df = df[df[x] != ""]

    if df.empty:
        raise ValueError(f"{x} 字段没有有效数据。")

    if aggregate == "count" or not y:
        final_df = (
            df
            .groupby(x)
            .size()
            .reset_index(name="数量")
        )

        value_col = "数量"

    elif aggregate == "mean":
        if y not in df.columns:
            raise ValueError(f"字段不存在：{y}")

        df[y] = pd.to_numeric(df[y], errors="coerce")
        df = df.dropna(subset=[y])

        if df.empty:
            raise ValueError(f"{y} 字段没有有效数值，不能计算平均值。")

        final_df = (
            df
            .groupby(x)[y]
            .mean()
            .reset_index(name=f"平均{y}")
        )

        value_col = f"平均{y}"

    elif aggregate == "sum":
        if y not in df.columns:
            raise ValueError(f"字段不存在：{y}")

        df[y] = pd.to_numeric(df[y], errors="coerce").fillna(0)

        final_df = (
            df
            .groupby(x)[y]
            .sum()
            .reset_index(name=f"{y}总和")
        )

        value_col = f"{y}总和"

    elif aggregate == "none":
        if not y:
            raise ValueError("未聚合图表必须提供 y 字段。")

        if y not in df.columns:
            raise ValueError(f"字段不存在：{y}")

        df[y] = pd.to_numeric(df[y], errors="coerce")

        final_df = df.dropna(subset=[y])[[x, y]].copy()

        if final_df.empty:
            raise ValueError(f"{y} 字段没有有效数值。")

        value_col = y

    else:
        raise ValueError(f"不支持的聚合方式：{aggregate}")

    if sort == "desc":
        final_df = final_df.sort_values(value_col, ascending=False)
    elif sort == "asc":
        final_df = final_df.sort_values(value_col, ascending=True)

    if top_n:
        final_df = final_df.head(top_n)

    return final_df.reset_index(drop=True), value_col


def prepare_scatter_chart_data(chart_df, x, y, size=None):
    """
    处理散点图数据，避免 Plotly size 出现 NaN。
    """

    df = chart_df.copy()

    if x not in df.columns:
        raise ValueError(f"字段不存在：{x}")

    if y not in df.columns:
        raise ValueError(f"字段不存在：{y}")

    df[x] = pd.to_numeric(df[x], errors="coerce")
    df[y] = pd.to_numeric(df[y], errors="coerce")

    df = df.dropna(subset=[x, y])

    if df.empty:
        raise ValueError("散点图的 x / y 字段没有足够的有效数值。")

    if size and size in df.columns:
        df[size] = pd.to_numeric(df[size], errors="coerce").fillna(0)
        df[size] = df[size].clip(lower=0)

    return df.reset_index(drop=True)


# =========================================================
# 数据摘要工具函数
# =========================================================

def build_column_summary(df):
    """
    生成字段完整度信息。
    """

    lines = []

    for col in df.columns:
        non_null_count = df[col].notna().sum()
        empty_text_count = 0

        if df[col].dtype == "object":
            empty_text_count = (df[col].astype(str).str.strip() == "").sum()

        valid_count = non_null_count - empty_text_count
        valid_ratio = valid_count / len(df) if len(df) > 0 else 0

        lines.append(
            f"- {col}：有效值 {valid_count} / {len(df)}，完整度 {valid_ratio:.1%}"
        )

    return "\n".join(lines)


def build_dataset_summary(df):
    """
    生成数据集摘要。
    """

    lines = []

    lines.append(f"书籍总数：{len(df)} 本")

    if "来源" in df.columns:
        source_counts = df["来源"].value_counts(dropna=False).to_dict()

        source_text = "；".join([
            f"{source}：{count} 本"
            for source, count in source_counts.items()
        ])

        lines.append(f"来源分布：{source_text}")

    if "评分" in df.columns:
        rating_series = pd.to_numeric(df["评分"], errors="coerce").dropna()

        if not rating_series.empty:
            lines.append(f"平均评分：{rating_series.mean():.2f}")
            lines.append(f"最高评分：{rating_series.max():.1f}")
            lines.append(f"最低评分：{rating_series.min():.1f}")
            lines.append(f"有评分数据的书籍数：{len(rating_series)} 本")
        else:
            lines.append("评分字段存在，但没有有效评分。")
    else:
        lines.append("缺少评分字段。")

    if "短评总赞" in df.columns:
        heat_series = pd.to_numeric(df["短评总赞"], errors="coerce").fillna(0)

        if heat_series.sum() > 0:
            lines.append(f"热度总量：{int(heat_series.sum())}")
            lines.append(f"最高热度值：{int(heat_series.max())}")
        else:
            lines.append("热度字段存在，但有效热度数据较少或全为 0。")
    else:
        lines.append("缺少热度字段。")

    if "出版年份" in df.columns:
        year_series = pd.to_numeric(df["出版年份"], errors="coerce").dropna()

        if not year_series.empty:
            lines.append(f"最早出版年份：{int(year_series.min())}")
            lines.append(f"最新出版年份：{int(year_series.max())}")
            lines.append(f"有出版年份的书籍数：{len(year_series)} 本")
        else:
            lines.append("出版年份字段存在，但没有有效年份。")
    else:
        lines.append("缺少出版年份字段。")

    if "标签" in df.columns:
        tags = extract_top_tags_from_series(df["标签"])

        if tags:
            lines.append("高频标签：" + "、".join(tags))
        else:
            lines.append("标签字段存在，但有效标签较少。")
    else:
        lines.append("缺少标签字段。")

    return "\n".join(lines)


def build_sample_books_text(df, max_rows=35):
    """
    取部分样本书籍传给 AI。
    """

    sample_df = df.head(max_rows)

    lines = []

    for _, row in sample_df.iterrows():
        title = safe_text(row.get("书名", "未知书名"))
        rating = safe_text(row.get("评分", ""))
        author = safe_text(row.get("作者/出版信息", ""))
        year = safe_text(row.get("出版年份", ""))
        heat = safe_text(row.get("短评总赞", ""))
        tags = safe_text(row.get("标签", ""))
        source = safe_text(row.get("来源", ""))
        intro = safe_text(row.get("短简介", ""))[:100]

        lines.append(
            f"- 《{title}》｜评分：{rating}｜作者/出版：{author}｜年份：{year}｜热度：{heat}｜标签：{tags}｜来源：{source}｜简介：{intro}"
        )

    return "\n".join(lines)


def get_numeric_series(df, col):
    """
    获取数值字段。
    """

    if col not in df.columns:
        return pd.Series(dtype=float)

    return pd.to_numeric(df[col], errors="coerce").dropna()


def get_numeric_columns(df):
    """
    获取可转为数值的字段。
    """

    numeric_columns = []

    for col in df.columns:
        numeric_series = pd.to_numeric(df[col], errors="coerce")

        if numeric_series.notna().sum() > 0:
            numeric_columns.append(col)

    return numeric_columns


def safe_text(value):
    """
    安全文本转换。
    """

    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass

    return str(value).replace("\n", " ").strip()


def clean_dimension_series(series):
    """
    清洗分类字段。
    例如出版年份是 1993.0 时，显示成 1993。
    """

    numeric_series = pd.to_numeric(series, errors="coerce")

    if len(series) > 0 and numeric_series.notna().sum() >= len(series) * 0.6:
        cleaned = numeric_series.apply(
            lambda x: str(int(x)) if pd.notna(x) and float(x).is_integer() else str(x)
        )

        cleaned = cleaned.replace("nan", "")

        return cleaned

    return (
        series
        .fillna("")
        .astype(str)
        .str.strip()
    )


def sort_by_dimension(df, x):
    """
    按维度字段排序。
    年份类字段会按数值排序。
    """

    final_df = df.copy()

    numeric_x = pd.to_numeric(final_df[x], errors="coerce")

    if numeric_x.notna().sum() > 0:
        final_df["_sort_x"] = numeric_x
        final_df = final_df.sort_values("_sort_x", ascending=True)
        final_df = final_df.drop(columns=["_sort_x"])

        return final_df.reset_index(drop=True)

    return final_df.sort_values(x, ascending=True).reset_index(drop=True)


def extract_top_tags_from_series(tag_series, top_n=10):
    """
    从标签列中提取高频标签。
    """

    tag_counts = {}

    for item in tag_series.dropna().astype(str):
        tags = split_tags(item)

        for tag in tags:
            if not tag:
                continue

            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    sorted_tags = sorted(
        tag_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return [tag for tag, _ in sorted_tags[:top_n]]


def explode_tags_dataframe(df, tag_col="标签"):
    """
    将标签列拆开成多行。
    """

    if tag_col not in df.columns:
        return df

    rows = []

    for _, row in df.iterrows():
        tags = split_tags(row.get(tag_col, ""))

        if not tags:
            continue

        for tag in tags:
            new_row = row.copy()
            new_row[tag_col] = tag
            rows.append(new_row)

    if not rows:
        return pd.DataFrame(columns=df.columns)

    return pd.DataFrame(rows)


def split_tags(text):
    """
    支持多种标签分隔符。
    """

    if not text:
        return []

    text = str(text)

    separators = ["，", ",", "、", "/", "|", ";", "；", " "]

    for sep in separators:
        text = text.replace(sep, ",")

    return [
        tag.strip()
        for tag in text.split(",")
        if tag.strip()
    ]


def clean_json_text(raw_text):
    """
    清理 AI 返回的 JSON 文本。
    """

    text = raw_text.strip()

    text = text.replace("```json", "")
    text = text.replace("```JSON", "")
    text = text.replace("```", "")

    return text.strip()


def make_key_suffix(text):
    """
    生成 Streamlit 组件 key 的安全后缀。
    """

    text = str(text)
    text = text.replace(" ", "_")
    text = text.replace("+", "plus")
    text = text.replace("/", "_")
    text = text.replace("\\", "_")

    return text