import ast
import pandas as pd


def parse_py_list(value):
    """
    把数据库里存储的字符串列表转成 Python list。
    例如：
    "[{'title': 'xxx', 'rate': '9.0'}]"
    """
    if isinstance(value, list):
        return value

    if value is None:
        return []

    if not isinstance(value, str):
        return []

    if value.strip() == "":
        return []

    try:
        return ast.literal_eval(value)
    except Exception:
        return []


def clean_books_df(df):
    df = df.copy()

    df["评分"] = pd.to_numeric(df["评分"], errors="coerce")

    df["相关推荐_list"] = df["相关推荐"].apply(parse_py_list)
    df["短评_list"] = df["短评"].apply(parse_py_list)

    df["短评总赞"] = df["短评_list"].apply(
        lambda comments: sum([comment.get("vote", 0) for comment in comments])
    )

    df["出版年份"] = (
        df["作者/出版信息"]
        .astype(str)
        .str.extract(r"(\d{4})")[0]
        .astype(float)
    )

    return df