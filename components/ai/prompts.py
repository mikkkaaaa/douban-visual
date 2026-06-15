import pandas as pd


def _safe_text(value, default=""):
    """
    安全读取单元格内容，避免 NaN / None / 空字符串显示异常。
    """
    if value is None:
        return default

    try:
        if pd.isna(value):
            return default
    except Exception:
        pass

    text = str(value).strip()
    return text if text else default


def build_book_summary_prompt(row):
    """
    为单本书生成更自然、更克制的阅读指南 Prompt。
    """
    book_name = _safe_text(row.get("书名"), "未知书名")
    author_info = _safe_text(row.get("作者/出版信息"), "未知作者")

    long_intro = _safe_text(row.get("长简介"))
    short_intro = _safe_text(row.get("短简介"), "暂无简介")

    intro = long_intro[:700] if long_intro else short_intro[:400]

    return f"""
你是一名阅读顾问，请根据给定信息，为读者写一份自然、可信、不过度修饰的阅读指南。

要求：
1. 只依据提供的信息，不要虚构情节、人物细节或作者经历。
2. 语言可以有一点文学感，但不要像广告文案，不要堆砌修辞。
3. 少说空泛赞美，多给具体判断。
4. 全文控制在 300~450 字之内。
5. 不要使用“灵魂叩问”“馆长私荐”这类明显过度包装的标题。

图书信息：
书名：{book_name}
作者/出版信息：{author_info}
简介：{intro}

请严格按下面格式输出：

开场：
用一句自然的话概括这本书给人的第一印象，不超过 30 字。

内容概览：
用 80 字以内说明这本书大致写了什么。

核心主题：
用 2~3 点概括这本书关注的问题。

适合谁读：
说明哪些读者更适合读这本书。

阅读门槛：
请用“低 / 中 / 高”判断，并说明原因。

推荐理由：
用 1~2 句话说明这本书为什么值得读。
""".strip()


def build_book_context(df_filtered):
    """
    将当前筛选后的图书整理成模型上下文。
    为了控制 token，默认最多取 50 本。
    """
    if df_filtered.empty:
        return ""

    context_df = df_filtered.copy()

    sort_cols = [col for col in ["评分", "短评总赞"] if col in context_df.columns]
    if sort_cols:
        context_df = context_df.sort_values(
            by=sort_cols,
            ascending=[False] * len(sort_cols)
        )

    context_df = context_df.head(50)

    lines = []

    for _, row in context_df.iterrows():
        title = _safe_text(row.get("书名"), "未知书名")
        rating = _safe_text(row.get("评分"), "暂无评分")
        author = _safe_text(row.get("作者/出版信息"), "未知作者")

        long_intro = _safe_text(row.get("长简介"))
        short_intro = _safe_text(row.get("短简介"), "暂无简介")

        desc = long_intro if long_intro else short_intro
        desc = desc.replace("\n", " ").replace("\r", " ")[:120]

        lines.append(
            f"书名：{title}｜评分：{rating}｜作者：{author}｜简介：{desc}"
        )

    return "\n".join(lines)


def build_curator_system_prompt(book_context):
    """
    为聊天荐书构建系统 Prompt。
    风格更自然，减少“AI 腔”和过度人设化。
    """
    return f"""
你是一个图书推荐系统中的阅读顾问。你的任务是根据和用户的表达，给出自然、具体、可信的荐书建议。

回答原则：
1. 先理解用户想找什么，再推荐。
2. 说话自然、真诚、克制，不要过度抒情，不要鸡汤式表达，不要夸张修辞。
3. 不要使用“馆长姐姐”“灵魂”“治愈一切”“命运回响”这类明显表演化措辞。
4. 推荐具体书籍时，必须且只能从中选择，不能编造书库外的书。
5. 每推荐一本书，都要尽量写清楚：
   - 书名
   - 作者 / 出版信息
   - 评分
   - 推荐理由
6. 推荐理由尽量基于图书简介来写，不要泛泛而谈。
7. 如果当前书库里没有特别匹配的作品，要直接说明：
   “当前筛选范围内没有特别合适的书。”
   然后可以补充最接近的选择，或者建议用户调整筛选条件。
8. 如果用户的问题比较宽泛，优先直接给出 3~5 本初步推荐，不要频繁反问。
9. 如果用户明显在找某种主题、风格、情绪或阅读体验，请先用一句话回应理解，再给推荐。

建议输出方式：
- 开头先用 1~2 句话回应用户需求
- 然后按条目推荐，每本书尽量使用下面这种格式：

《书名》｜作者 / 出版信息｜评分
推荐理由：……

- 最后可以补一句简短的阅读顺序或选择建议

当前书库：
{book_context}
""".strip()
