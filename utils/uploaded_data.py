import pandas as pd


COLUMN_MAP = {
    "书名": ["书名", "标题", "图书名称", "title", "name", "book_name"],
    "作者": ["作者", "作者名", "author"],
    "评分": ["评分", "豆瓣评分", "rating", "score"],
    "出版年份": ["出版年份", "年份", "出版年", "year", "publish_year"],
    "评论数": ["评论数", "评价人数", "短评数", "comment_count", "comments", "votes"],
    "简介": ["简介", "短简介", "内容简介", "intro", "description", "summary"],
    "标签": ["标签", "分类", "类型", "tags", "category"]
}


def read_uploaded_file(uploaded_file):
    """
    读取用户上传的 CSV 或 Excel 文件。
    """
    file_name = uploaded_file.name.lower()

    if file_name.endswith(".csv"):
        try:
            return pd.read_csv(uploaded_file, encoding="utf-8")
        except UnicodeDecodeError:
            uploaded_file.seek(0)
            return pd.read_csv(uploaded_file, encoding="gbk")

    if file_name.endswith(".xlsx") or file_name.endswith(".xls"):
        return pd.read_excel(uploaded_file)

    raise ValueError("仅支持 CSV、XLSX、XLS 文件")


def find_column(df, candidates):
    """
    根据候选字段名查找上传表格里的真实列名。
    """
    lower_cols = {
        str(col).strip().lower(): col
        for col in df.columns
    }

    for candidate in candidates:
        key = candidate.strip().lower()
        if key in lower_cols:
            return lower_cols[key]

    return None


def normalize_uploaded_books(df):
    """
    将不同用户上传的数据字段统一成系统需要的格式。
    """
    df = df.copy()

    normalized = pd.DataFrame()

    for standard_col, candidates in COLUMN_MAP.items():
        matched_col = find_column(df, candidates)

        if matched_col:
            normalized[standard_col] = df[matched_col]
        else:
            normalized[standard_col] = None

    normalized["书名"] = normalized["书名"].fillna("").astype(str).str.strip()
    normalized = normalized[normalized["书名"] != ""]

    normalized["作者"] = normalized["作者"].fillna("").astype(str).str.strip()
    normalized["简介"] = normalized["简介"].fillna("").astype(str).str.strip()
    normalized["标签"] = normalized["标签"].fillna("").astype(str).str.strip()

    normalized["评分"] = pd.to_numeric(normalized["评分"], errors="coerce")
    normalized["出版年份"] = pd.to_numeric(normalized["出版年份"], errors="coerce")
    normalized["评论数"] = pd.to_numeric(normalized["评论数"], errors="coerce")

    normalized["出版年份"] = normalized["出版年份"].astype("Int64")
    normalized["评论数"] = normalized["评论数"].astype("Int64")

    return normalized