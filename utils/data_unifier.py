import pandas as pd


UNIFIED_COLUMNS = [
    "数据ID",
    "书名",
    "评分",
    "作者/出版信息",
    "出版年份",
    "短简介",
    "长简介",
    "短评总赞",
    "链接",
    "标签",
    "来源",
    "原始来源文件",
    "相关推荐_list",
    "短评_list"
]


def make_empty_unified_df():
    """
    创建一个空的统一书籍 DataFrame。
    """
    return pd.DataFrame(columns=UNIFIED_COLUMNS)


def get_column(df, column_name, default=None):
    """
    安全读取字段。
    如果字段不存在，就返回同长度的默认值列。
    """
    if column_name in df.columns:
        return df[column_name]

    return pd.Series([default] * len(df), index=df.index)


def to_numeric_series(series):
    """
    安全转换为数值类型。
    """
    return pd.to_numeric(series, errors="coerce")


def normalize_text_series(series):
    """
    将字段统一转成文本，并处理空值。
    """
    return (
        series
        .fillna("")
        .astype(str)
        .str.strip()
    )


def normalize_list_series(series):
    """
    保证相关推荐_list、短评_list 这类字段是列表。
    如果不是列表，就转为空列表。
    """
    return series.apply(lambda value: value if isinstance(value, list) else [])


def normalize_public_books(public_df):
    """
    将公共豆瓣书库 books 表数据转换成统一字段格式。

    公共书库原始字段通常包括：
    - 书名
    - 评分
    - 作者/出版信息
    - 出版年份
    - 短简介
    - 长简介
    - 短评总赞
    - 链接
    - 相关推荐_list
    - 短评_list
    """

    if public_df is None or public_df.empty:
        return make_empty_unified_df()

    df = public_df.copy()
    unified = pd.DataFrame(index=df.index)

    unified["数据ID"] = get_column(df, "id", None)
    unified["书名"] = normalize_text_series(get_column(df, "书名", ""))
    unified["评分"] = to_numeric_series(get_column(df, "评分", None))
    unified["作者/出版信息"] = normalize_text_series(get_column(df, "作者/出版信息", ""))
    unified["出版年份"] = to_numeric_series(get_column(df, "出版年份", None))
    unified["短简介"] = normalize_text_series(get_column(df, "短简介", ""))
    unified["长简介"] = normalize_text_series(get_column(df, "长简介", ""))
    unified["短评总赞"] = to_numeric_series(get_column(df, "评论数", 0)).fillna(0)
    unified["链接"] = normalize_text_series(get_column(df, "链接", ""))
    unified["标签"] = normalize_text_series(get_column(df, "标签", ""))

    unified["来源"] = "公共书库"
    unified["原始来源文件"] = ""

    unified["相关推荐_list"] = normalize_list_series(get_column(df, "相关推荐_list", []))
    unified["短评_list"] = normalize_list_series(get_column(df, "短评_list", []))

    unified = unified[UNIFIED_COLUMNS]

    # 没有书名的数据不要进入展示和分析
    unified = unified[unified["书名"] != ""]

    return unified.reset_index(drop=True)


def normalize_user_books(user_df):
    """
    将用户个人书库 user_books 表数据转换成统一字段格式。

    用户书库字段通常包括：
    - id
    - 书名
    - 作者
    - 评分
    - 出版年份
    - 评论数
    - 简介
    - 标签
    - 来源文件

    转换规则：
    - 作者 -> 作者/出版信息
    - 简介 -> 短简介
    - 简介 -> 长简介
    - 评论数 -> 短评总赞
    - 来源 -> 我的书库
    """

    if user_df is None or user_df.empty:
        return make_empty_unified_df()

    df = user_df.copy()
    unified = pd.DataFrame(index=df.index)

    unified["数据ID"] = get_column(df, "id", None)
    unified["书名"] = normalize_text_series(get_column(df, "书名", ""))
    unified["评分"] = to_numeric_series(get_column(df, "评分", None))
    unified["作者/出版信息"] = normalize_text_series(get_column(df, "作者", ""))
    unified["出版年份"] = to_numeric_series(get_column(df, "出版年份", None))

    intro_series = normalize_text_series(get_column(df, "简介", ""))
    unified["短简介"] = intro_series
    unified["长简介"] = intro_series

    unified["短评总赞"] = to_numeric_series(get_column(df, "评论数", 0)).fillna(0)
    unified["链接"] = ""
    unified["标签"] = normalize_text_series(get_column(df, "标签", ""))

    unified["来源"] = "我的书库"
    unified["原始来源文件"] = normalize_text_series(get_column(df, "来源文件", ""))

    # 用户上传的数据一般没有相关推荐和短评结构，所以统一设为空列表
    unified["相关推荐_list"] = [[] for _ in range(len(df))]
    unified["短评_list"] = [[] for _ in range(len(df))]

    unified = unified[UNIFIED_COLUMNS]

    unified = unified[unified["书名"] != ""]

    return unified.reset_index(drop=True)


def combine_books(public_df, user_df):
    """
    合并公共书库和个人书库。
    注意：这里只是页面层合并，不会把用户数据写入公共 books 表。
    """

    public_books = normalize_public_books(public_df)
    user_books = normalize_user_books(user_df)

    if public_books.empty and user_books.empty:
        return make_empty_unified_df()

    combined = pd.concat(
        [public_books, user_books],
        ignore_index=True
    )

    return combined


def get_source_label(source_mode):
    """
    数据源模式显示名称。
    """
    source_labels = {
        "public": "公共书库",
        "user": "我的书库",
        "combined": "公共书库 + 我的书库"
    }

    return source_labels.get(source_mode, "公共书库")