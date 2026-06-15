import ast
import json
import re
from typing import Any

import pandas as pd
from snownlp import SnowNLP


COMMENT_TEXT_KEYS = [
    "短评",
    "评论",
    "内容",
    "comment",
    "text",
    "content",
    "summary"
]

COMMENT_VOTE_KEYS = [
    "赞同数",
    "有用数",
    "赞",
    "votes",
    "vote",
    "likes",
    "like_count"
]


def analyze_comment_sentiment(df_books: pd.DataFrame, max_comments_per_book: int = 20):
    """
    对图书热门短评进行情感分析。

    输入：
    df_books: 当前筛选后的图书 DataFrame，需要尽量包含：
        - 书名
        - 评分
        - 短评总赞
        - 短评_list

    输出：
    comment_df: 每条短评的情感分析结果
    book_sentiment_df: 按图书聚合后的情感分析结果
    """

    comment_columns = [
        "书名",
        "评分",
        "短评",
        "赞同数",
        "情感得分",
        "情感标签"
    ]

    book_columns = [
        "书名",
        "评分",
        "情感均值",
        "短评数量",
        "积极占比",
        "中性占比",
        "消极占比",
        "短评总赞"
    ]

    if df_books is None or df_books.empty:
        return pd.DataFrame(columns=comment_columns), pd.DataFrame(columns=book_columns)

    rows = []

    for _, book_row in df_books.iterrows():
        book_name = safe_text(book_row.get("书名", "未知图书"))
        rating = to_float(book_row.get("评分", None))
        total_votes = to_int(book_row.get("短评总赞", 0))

        raw_comments = None

        for possible_col in ["短评_list", "热门短评", "短评", "评论_list"]:
            if possible_col in df_books.columns:
                raw_comments = book_row.get(possible_col)
                if not is_empty_value(raw_comments):
                    break

        comments = parse_comment_list(raw_comments)

        if not comments:
            continue

        for item in comments[:max_comments_per_book]:
            comment_text, vote_count = parse_comment_item(item)

            comment_text = clean_comment_text(comment_text)

            if not comment_text:
                continue

            score = get_sentiment_score(comment_text)
            label = get_sentiment_label(score)

            rows.append({
                "书名": book_name,
                "评分": rating,
                "短评": comment_text,
                "赞同数": vote_count,
                "短评总赞": total_votes,
                "情感得分": score,
                "情感标签": label
            })

    comment_df = pd.DataFrame(rows)

    if comment_df.empty:
        return pd.DataFrame(columns=comment_columns), pd.DataFrame(columns=book_columns)

    comment_df["评分"] = pd.to_numeric(comment_df["评分"], errors="coerce")
    comment_df["赞同数"] = pd.to_numeric(comment_df["赞同数"], errors="coerce").fillna(0).astype(int)
    comment_df["短评总赞"] = pd.to_numeric(comment_df["短评总赞"], errors="coerce").fillna(0).astype(int)
    comment_df["情感得分"] = pd.to_numeric(comment_df["情感得分"], errors="coerce").fillna(0.5)

    book_sentiment_df = (
        comment_df
        .groupby("书名", as_index=False)
        .agg(
            评分=("评分", "mean"),
            情感均值=("情感得分", "mean"),
            短评数量=("短评", "count"),
            短评总赞=("短评总赞", "max")
        )
    )

    for label in ["积极", "中性", "消极"]:
        label_ratio = (
            comment_df
            .assign(is_label=comment_df["情感标签"].eq(label))
            .groupby("书名")["is_label"]
            .mean()
            .mul(100)
        )

        book_sentiment_df[f"{label}占比"] = (
            book_sentiment_df["书名"]
            .map(label_ratio)
            .fillna(0)
        )

    return comment_df, book_sentiment_df


def parse_comment_list(value: Any):
    """
    兼容数据库里不同形式的短评字段：
    1. Python list
    2. JSON 字符串
    3. Python repr 字符串
    4. 单条普通文本
    """

    if is_empty_value(value):
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, tuple):
        return list(value)

    if isinstance(value, dict):
        return [value]

    text = str(value).strip()

    if not text or text in ["[]", "{}", "None", "nan", "NaN"]:
        return []

    for parser in [json.loads, ast.literal_eval]:
        try:
            parsed = parser(text)

            if isinstance(parsed, list):
                return parsed

            if isinstance(parsed, tuple):
                return list(parsed)

            if isinstance(parsed, dict):
                return [parsed]

            if isinstance(parsed, str):
                return [parsed]

        except Exception:
            pass

    if len(text) >= 5:
        return [text]

    return []


def parse_comment_item(item: Any):
    """
    将单条短评统一解析成：
    comment_text, vote_count
    """

    if isinstance(item, dict):
        comment_text = ""

        for key in COMMENT_TEXT_KEYS:
            if key in item and not is_empty_value(item.get(key)):
                comment_text = item.get(key)
                break

        vote_count = 0

        for key in COMMENT_VOTE_KEYS:
            if key in item and not is_empty_value(item.get(key)):
                vote_count = to_int(item.get(key))
                break

        return comment_text, vote_count

    return str(item), 0


def get_sentiment_score(text: str) -> float:
    """
    SnowNLP 的 sentiments 返回 0 到 1：
    越接近 1 表示越积极，越接近 0 表示越消极。
    """

    try:
        score = float(SnowNLP(text).sentiments)
    except Exception:
        score = 0.5

    if score < 0:
        return 0.0

    if score > 1:
        return 1.0

    return score


def get_sentiment_label(score: float) -> str:
    if score >= 0.6:
        return "积极"

    if score <= 0.4:
        return "消极"

    return "中性"


def clean_comment_text(text: Any) -> str:
    text = safe_text(text)

    if not text:
        return ""

    text = re.sub(r"\s+", " ", text)
    text = text.strip()

    return text


def safe_text(value: Any) -> str:
    if is_empty_value(value):
        return ""

    return str(value).strip()


def to_float(value: Any):
    try:
        if is_empty_value(value):
            return None

        return float(value)
    except Exception:
        return None


def to_int(value: Any, default: int = 0) -> int:
    try:
        if is_empty_value(value):
            return default

        text = str(value)
        numbers = re.findall(r"\d+", text)

        if not numbers:
            return default

        return int(numbers[0])
    except Exception:
        return default


def is_empty_value(value: Any) -> bool:
    if value is None:
        return True

    if isinstance(value, float) and pd.isna(value):
        return True

    if isinstance(value, str) and value.strip() in ["", "None", "nan", "NaN", "null"]:
        return True

    return False