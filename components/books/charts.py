import tempfile
import pandas as pd
import streamlit as st
import plotly.express as px
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components


def render_book_charts(df_filtered):
    if df_filtered.empty:
        st.warning("暂无数据进行可视化，请放宽筛选条件。")
        return

    st.markdown("""
    本模块从评分、短评热度、出版年份、短评情感和推荐关系等角度，
    对当前筛选结果进行多维度可视化分析。
    """)

    chart_options = render_chart_controls(df_filtered)

    st.subheader("当前筛选数据预览")

    preview_cols = [
        "书名",
        "评分",
        "作者/出版信息",
        "出版年份",
        "短评总赞"
    ]

    preview_df = df_filtered[
        [col for col in preview_cols if col in df_filtered.columns]
    ]

    st.dataframe(
        preview_df,
        use_container_width=True,
        height=300
    )

    st.divider()

    render_data_insights(df_filtered)

    st.divider()

    st.subheader("评分与热度分析")

    col1, col2 = st.columns(2)

    with col1:
        render_top_rating_chart(df_filtered, chart_options["top_n"])

    with col2:
        render_top_votes_chart(df_filtered, chart_options["top_n"])

    render_rating_votes_scatter(df_filtered)

    st.divider()
    st.subheader("出版时间趋势分析")
    render_year_rating_chart(df_filtered)

    st.divider()
    render_sentiment_analysis(df_filtered)

    st.divider()
    render_network_chart(df_filtered, chart_options["network_limit"])


def render_chart_controls(df_filtered):
    st.subheader("图表筛选控制")

    max_top_n = min(50, len(df_filtered))
    min_top_n = min(5, max_top_n)
    default_top_n = min(20, max_top_n)

    col1, col2 = st.columns(2)

    with col1:
        top_n = st.slider(
            "Top 榜单展示数量",
            min_value=min_top_n,
            max_value=max_top_n,
            value=default_top_n,
            step=1 if max_top_n < 5 else 5,
            help="控制评分 Top 和热度 Top 图表展示的书籍数量。"
        )

    with col2:
        max_network_nodes = min(120, len(df_filtered))
        min_network_nodes = min(5, max_network_nodes)
        default_network_nodes = min(60, max_network_nodes)

        network_limit = st.slider(
            "网络图最多节点数",
            min_value=min_network_nodes,
            max_value=max_network_nodes,
            value=default_network_nodes,
            step=1 if max_network_nodes < 5 else 5,
            help="网络图节点越多越容易卡顿，建议答辩演示时控制在 60 个以内。"
        )

    st.caption(
        "这些控制只影响当前页面图表展示，不会修改数据库或原始数据。"
    )

    return {
        "top_n": top_n,
        "network_limit": network_limit
    }


def render_data_insights(df_filtered):
    st.subheader("当前筛选结果数据洞察")

    avg_rating = df_filtered["评分"].mean()
    max_rating_row = df_filtered.sort_values("评分", ascending=False).iloc[0]
    hot_row = df_filtered.sort_values("短评总赞", ascending=False).iloc[0]

    year_data = df_filtered["出版年份"].dropna()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.info(
            f"当前筛选结果的平均评分为 **{avg_rating:.2f}**，"
            f"说明该区间图书整体评价较高。"
        )

    with col2:
        st.success(
            f"当前最高评分图书为 **《{max_rating_row['书名']}》**，"
            f"评分达到 **{max_rating_row['评分']}**。"
        )

    with col3:
        st.warning(
            f"当前短评热度最高的是 **《{hot_row['书名']}》**，"
            f"短评总赞数为 **{int(hot_row['短评总赞'])}**。"
        )

    if not year_data.empty:
        year_min = int(year_data.min())
        year_max = int(year_data.max())

        st.markdown(
            f"""
             **时间跨度分析**：当前数据覆盖出版年份约从 **{year_min} 年** 到 **{year_max} 年**。
            这说明豆瓣 Top250 中既包含长期沉淀的经典作品，也包含较新的大众阅读作品。
            """
        )


def render_top_rating_chart(df_filtered, top_n=20):
    df_top_rating = df_filtered.sort_values("评分", ascending=False).head(top_n).copy()
    df_top_rating["rank"] = range(1, len(df_top_rating) + 1)

    fig = px.bar(
        df_top_rating,
        x="书名",
        y="评分",
        text=df_top_rating["评分"].apply(lambda x: f"{x:.1f}"),
        color="rank",
        color_continuous_scale=px.colors.sequential.Plasma,
        title=f"评分 Top{len(df_top_rating)}"
    )

    fig.update_layout(
        xaxis_tickangle=-45,
        showlegend=False,
        yaxis=dict(range=[8.5, 10])
    )

    st.plotly_chart(fig, use_container_width=True)
    render_chart_conclusion(
        "分析结论",
        build_top_rating_conclusion(df_top_rating)
    )


def render_top_votes_chart(df_filtered, top_n=20):
    if "短评总赞" not in df_filtered.columns:
        st.info("当前数据缺少短评热度字段，暂不能生成热度 Top 图。")
        return

    df_top_votes = df_filtered.sort_values("短评总赞", ascending=False).head(top_n).copy()
    df_top_votes["rank"] = range(1, len(df_top_votes) + 1)

    fig = px.bar(
        df_top_votes,
        x="书名",
        y="短评总赞",
        text="短评总赞",
        color="rank",
        color_continuous_scale=px.colors.sequential.Viridis,
        title=f"热度 Top{len(df_top_votes)}：短评总赞数"
    )

    fig.update_layout(
        xaxis_tickangle=-45,
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)
    render_chart_conclusion(
        "分析结论",
        build_top_votes_conclusion(df_top_votes)
    )


def render_rating_votes_scatter(df_filtered):
    """
    评分与热度关系散点图。
    兼容公共书库、我的书库、公共 + 我的书库。
    """

    st.subheader("评分与热度关系")

    if df_filtered.empty:
        st.info("当前数据为空，暂不能生成评分与热度散点图。")
        return

    if "评分" not in df_filtered.columns:
        st.info("当前数据缺少评分字段，暂不能生成评分与热度散点图。")
        return

    scatter_df = df_filtered.copy()

    # 关键修复：评分转数字
    scatter_df["评分"] = pd.to_numeric(
        scatter_df["评分"],
        errors="coerce"
    )

    # 关键修复：短评总赞不存在就创建，存在就转数字并填 0
    if "短评总赞" not in scatter_df.columns:
        scatter_df["短评总赞"] = 0
    else:
        scatter_df["短评总赞"] = pd.to_numeric(
            scatter_df["短评总赞"],
            errors="coerce"
        ).fillna(0)

    # 删除没有评分的数据
    scatter_df = scatter_df.dropna(subset=["评分"])

    if scatter_df.empty:
        st.info("当前数据中没有有效评分，暂不能生成评分与热度散点图。")
        return

    # 气泡大小不能有 NaN，也不能全是 NaN
    scatter_df["气泡大小"] = scatter_df["短评总赞"].fillna(0).clip(lower=0)

    hover_cols = []

    for col in ["作者/出版信息", "出版年份", "来源", "标签"]:
        if col in scatter_df.columns:
            hover_cols.append(col)

    # 如果所有热度都是 0，不使用 size 参数，避免 Plotly 报错
    if scatter_df["气泡大小"].sum() <= 0:
        fig = px.scatter(
            scatter_df,
            x="短评总赞",
            y="评分",
            hover_name="书名" if "书名" in scatter_df.columns else None,
            hover_data=hover_cols,
            title="评分与热度关系"
        )

        st.plotly_chart(fig, use_container_width=True)

        st.caption(
            "当前数据源缺少有效热度数据，因此散点图未使用气泡大小。"
        )
        render_chart_conclusion(
            "分析结论",
            "当前数据缺少有效热度值，只能观察评分分布，暂不适合判断评分与讨论热度之间的关系。"
        )

    else:
        # 再次确保绝对没有 NaN
        scatter_df["气泡大小"] = scatter_df["气泡大小"].fillna(0)

        fig = px.scatter(
            scatter_df,
            x="短评总赞",
            y="评分",
            size="气泡大小",
            hover_name="书名" if "书名" in scatter_df.columns else None,
            hover_data=hover_cols,
            size_max=45,
            title="评分与热度关系"
        )

        st.plotly_chart(fig, use_container_width=True)

        st.caption(
            "散点图用于观察图书评分与讨论热度之间的关系。气泡越大，表示短评赞数或评论热度越高。"
        )
        render_chart_conclusion(
            "分析结论",
            build_rating_heat_conclusion(scatter_df)
        )

def render_year_rating_chart(df_filtered):
    df_year = (
        df_filtered
        .dropna(subset=["出版年份"])
        .groupby("出版年份")["评分"]
        .mean()
        .reset_index()
    )

    if df_year.empty:
        st.info("当前筛选结果暂无有效出版年份数据。")
        return

    fig = px.line(
        df_year,
        x="出版年份",
        y="评分",
        markers=True,
        title="出版年份 vs 平均评分"
    )

    st.plotly_chart(fig, use_container_width=True)
    render_chart_conclusion(
        "分析结论",
        build_year_rating_conclusion(df_year)
    )


def render_sentiment_analysis(df_filtered):
    st.subheader("热门短评情感分析")

    st.markdown("""
    本模块基于图书热门短评文本进行情感倾向分析，将短评分为积极、中性、消极三类，
    用于观察读者评论情绪与图书评分、热度之间的关系。
    """)

    if "短评_list" not in df_filtered.columns:
        st.info("当前数据缺少短评字段，暂不能进行短评情感分析。请确认 books 表中存在 短评_list 字段。")
        return

    with st.expander("分析方法说明", expanded=False):
        st.markdown("""
        本模块使用 SnowNLP 对中文短评进行情感倾向判断。

        情感得分范围为 0 到 1：

        - 大于等于 0.6：积极
        - 0.4 到 0.6：中性
        - 小于等于 0.4：消极

        分析结果用于辅助观察读者评论倾向，不能等同于严格的人工标注结果。
        """)

    if not st.checkbox("运行短评情感分析", key="run_comment_sentiment_analysis"):
        st.caption("勾选后将对当前筛选结果中的热门短评进行情感分析。")
        return

    try:
        from utils.sentiment_analyzer import analyze_comment_sentiment
    except ModuleNotFoundError:
        st.warning("缺少情感分析依赖。请在 requirements.txt 中添加 snownlp，然后重新部署。")
        st.code("snownlp", language="text")
        return
    except Exception as e:
        st.error(f"情感分析模块加载失败：{e}")
        return

    with st.spinner("正在分析短评情感，请稍候..."):
        comment_df, book_sentiment_df = analyze_comment_sentiment(df_filtered)

    if comment_df.empty:
        st.info("当前筛选结果中暂无可用于情感分析的短评数据。")
        return

    positive_ratio = comment_df["情感标签"].eq("积极").mean() * 100
    neutral_ratio = comment_df["情感标签"].eq("中性").mean() * 100
    negative_ratio = comment_df["情感标签"].eq("消极").mean() * 100

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("短评样本数", len(comment_df))

    with col2:
        st.metric("平均情感得分", f"{comment_df['情感得分'].mean():.2f}")

    with col3:
        st.metric("积极短评占比", f"{positive_ratio:.1f}%")

    with col4:
        st.metric("消极短评占比", f"{negative_ratio:.1f}%")

    st.caption(
        f"当前样本中，中性短评占比为 {neutral_ratio:.1f}%。"
    )
    render_chart_conclusion(
        "分析结论",
        build_sentiment_conclusion(
            positive_ratio=positive_ratio,
            neutral_ratio=neutral_ratio,
            negative_ratio=negative_ratio,
            avg_score=comment_df["情感得分"].mean()
        )
    )

    col_a, col_b = st.columns(2)

    with col_a:
        label_count = (
            comment_df["情感标签"]
            .value_counts()
            .rename_axis("情感标签")
            .reset_index(name="数量")
        )

        fig_label = px.pie(
            label_count,
            names="情感标签",
            values="数量",
            title="短评情感倾向分布"
        )

        st.plotly_chart(fig_label, use_container_width=True)

    with col_b:
        fig_hist = px.histogram(
            comment_df,
            x="情感得分",
            nbins=20,
            title="短评情感得分分布"
        )

        fig_hist.update_xaxes(range=[0, 1])

        st.plotly_chart(fig_hist, use_container_width=True)

    if not book_sentiment_df.empty:
        st.markdown("### 图书评分与短评情感关系")

        scatter_df = book_sentiment_df.copy()

        scatter_df["评分"] = pd.to_numeric(
            scatter_df["评分"],
            errors="coerce"
        )

        scatter_df["情感均值"] = pd.to_numeric(
            scatter_df["情感均值"],
            errors="coerce"
        )

        scatter_df["短评数量"] = pd.to_numeric(
            scatter_df["短评数量"],
            errors="coerce"
        ).fillna(1).clip(lower=1)

        scatter_df = scatter_df.dropna(subset=["评分", "情感均值"])

        if scatter_df.empty:
            st.info("当前数据缺少有效评分或情感均值，暂不能生成评分与情感关系图。")
        else:
            fig_scatter = px.scatter(
                scatter_df,
                x="评分",
                y="情感均值",
                size="短评数量",
                hover_data=[
                    "书名",
                    "短评数量",
                    "积极占比",
                    "中性占比",
                    "消极占比"
                ],
                title="图书评分 vs 短评平均情感得分",
                labels={
                    "评分": "豆瓣评分",
                    "情感均值": "短评平均情感得分"
                },
                size_max=50
            )

            fig_scatter.update_yaxes(range=[0, 1])

            st.plotly_chart(fig_scatter, use_container_width=True)

        st.markdown("### 情感得分较高的图书 Top10")

        top_positive = (
            book_sentiment_df
            .sort_values("情感均值", ascending=False)
            .head(10)
        )

        fig_top_positive = px.bar(
            top_positive,
            x="情感均值",
            y="书名",
            orientation="h",
            title="短评情感均值 Top10",
            text=top_positive["情感均值"].apply(lambda x: f"{x:.2f}")
        )

        fig_top_positive.update_xaxes(range=[0, 1])
        fig_top_positive.update_layout(
            yaxis=dict(categoryorder="total ascending")
        )

        st.plotly_chart(fig_top_positive, use_container_width=True)

        st.markdown("### 情感得分较低的图书 Top10")

        top_negative = (
            book_sentiment_df
            .sort_values("情感均值", ascending=True)
            .head(10)
        )

        fig_top_negative = px.bar(
            top_negative,
            x="情感均值",
            y="书名",
            orientation="h",
            title="短评情感均值较低的图书 Top10",
            text=top_negative["情感均值"].apply(lambda x: f"{x:.2f}")
        )

        fig_top_negative.update_xaxes(range=[0, 1])
        fig_top_negative.update_layout(
            yaxis=dict(categoryorder="total descending")
        )

        st.plotly_chart(fig_top_negative, use_container_width=True)

    st.markdown("### 短评情感明细")

    display_cols = [
        "书名",
        "短评",
        "赞同数",
        "情感得分",
        "情感标签"
    ]

    st.dataframe(
        comment_df[[col for col in display_cols if col in comment_df.columns]],
        use_container_width=True,
        height=320
    )


def render_network_chart(df_filtered, network_limit=None):
    st.subheader("书籍推荐关系网络图")

    st.markdown("""
    网络图根据每本书的相关推荐关系构建：节点代表书籍，连线代表两本书在推荐列表中互相关联。
    该图更适合观察当前筛选范围内是否存在明显的阅读主题群。
    """)

    if not st.checkbox("生成并渲染网络图"):
        st.caption("网络图需要额外渲染 HTML，默认不自动生成，以避免页面加载过慢。")
        return

    if len(df_filtered) == 0:
        st.info("当前筛选条件下没有可用于生成网络图的数据。")
        return

    if "相关推荐_list" not in df_filtered.columns:
        st.info("当前数据缺少相关推荐字段，暂不能生成推荐关系网络。")
        return

    max_nodes = min(120, len(df_filtered))
    network_limit = min(network_limit or max_nodes, max_nodes)

    network_df = df_filtered.head(network_limit)

    st.caption(
        f"当前网络图展示前 {network_limit} 本书。若节点过多或浏览器卡顿，请调低上方网络图节点数。"
    )

    with st.spinner("正在绘制关系网..."):
        G = nx.Graph()

        book_names = set(network_df["书名"].values)

        for _, row in network_df.iterrows():
            G.add_node(
                row["书名"],
                title=row["书名"],
                rating=row["评分"]
            )

            for rec in row["相关推荐_list"]:
                if isinstance(rec, dict) and rec.get("title") in book_names:
                    G.add_edge(row["书名"], rec["title"])

        edge_count = len(G.edges)
        isolated_count = len(list(nx.isolates(G)))

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("网络节点数", len(G.nodes))
        with col2:
            st.metric("推荐连线数", edge_count)
        with col3:
            st.metric("孤立节点数", isolated_count)

        if len(G.nodes) == 0 or edge_count == 0:
            st.info("当前书籍之间没有发现足够的关联推荐。")
            st.caption(
                "可以扩大左侧筛选范围，或提高网络图节点数量，让更多书籍进入关系计算。"
            )
            return

        net = Network(
            height="600px",
            width="100%",
            bgcolor="#ffffff",
            font_color="black",
            cdn_resources="in_line"
        )

        net.from_nx(G)

        for node in net.nodes:
            node["color"] = "#3498db"
            node["size"] = 15
            node["title"] = f"{node['id']} ({node.get('rating', '无评分')})"

        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".html")
        tmp_path = tmp_file.name
        tmp_file.close()

        net.save_graph(tmp_path)

        with open(tmp_path, "r", encoding="utf-8") as f:
            components.html(f.read(), height=600)

        density = nx.density(G)
        render_chart_conclusion(
            "分析结论",
            (
                f"当前网络包含 {len(G.nodes)} 个节点、{edge_count} 条推荐关系，"
                f"网络密度约为 {density:.3f}。"
                "连线越密集，说明当前筛选范围内图书之间的推荐关联越集中；"
                "孤立节点较多时，说明这些书与当前样本中的其他书关联较弱。"
            )
        )


def render_chart_conclusion(title, text):
    if not text:
        return

    st.info(f"**{title}：** {text}")


def build_top_rating_conclusion(df_top_rating):
    if df_top_rating.empty:
        return ""

    top_book = df_top_rating.iloc[0]
    avg_rating = df_top_rating["评分"].mean()
    min_rating = df_top_rating["评分"].min()

    return (
        f"当前 Top 榜首为《{top_book['书名']}》，评分 {top_book['评分']:.1f}。"
        f"榜单平均评分为 {avg_rating:.2f}，最低也达到 {min_rating:.1f}，"
        "说明当前筛选结果中的高分作品集中度较高。"
    )


def build_top_votes_conclusion(df_top_votes):
    if df_top_votes.empty:
        return ""

    top_book = df_top_votes.iloc[0]
    total_votes = pd.to_numeric(df_top_votes["短评总赞"], errors="coerce").fillna(0).sum()
    top_ratio = 0

    if total_votes > 0:
        top_ratio = top_book["短评总赞"] / total_votes * 100

    return (
        f"当前热度最高的是《{top_book['书名']}》，短评总赞为 {int(top_book['短评总赞'])}。"
        f"它约占当前热度榜样本总赞数的 {top_ratio:.1f}%，"
        "可作为观察大众讨论集中度的重点对象。"
    )


def build_rating_heat_conclusion(scatter_df):
    if scatter_df.empty or len(scatter_df) < 3:
        return "当前有效样本较少，评分与热度关系只能作为参考。"

    corr = scatter_df[["评分", "短评总赞"]].corr().iloc[0, 1]

    if pd.isna(corr):
        return "当前热度数据变化较小，暂不能形成稳定的相关性判断。"

    if corr >= 0.4:
        relation = "评分与热度呈现较明显的正相关，高评分作品往往也更容易获得讨论。"
    elif corr <= -0.4:
        relation = "评分与热度呈现一定负相关，说明高讨论度作品不一定评分最高。"
    else:
        relation = "评分与热度相关性不强，说明读者讨论热度和评分评价并不完全同步。"

    return f"{relation} 当前相关系数约为 {corr:.2f}。"


def build_year_rating_conclusion(df_year):
    if df_year.empty:
        return ""

    best_year = df_year.sort_values("评分", ascending=False).iloc[0]
    year_count = len(df_year)

    return (
        f"当前共有 {year_count} 个出版年份进入统计，"
        f"平均评分最高的年份是 {int(best_year['出版年份'])} 年，均分 {best_year['评分']:.2f}。"
        "由于部分年份样本可能较少，年份均分更适合观察趋势，不宜单独作为质量判断。"
    )


def build_sentiment_conclusion(positive_ratio, neutral_ratio, negative_ratio, avg_score):
    if positive_ratio >= max(neutral_ratio, negative_ratio):
        main_tone = "积极短评占比最高，说明当前样本整体评论情绪偏正向。"
    elif negative_ratio >= max(positive_ratio, neutral_ratio):
        main_tone = "消极短评占比最高，说明当前样本中存在较多批评或争议表达。"
    else:
        main_tone = "中性短评占比最高，说明当前样本评论更偏描述和理性表达。"

    return (
        f"{main_tone} 平均情感得分为 {avg_score:.2f}。"
        "SnowNLP 结果适合作为辅助观察，遇到反讽、复杂长句时仍可能存在误判。"
    )
