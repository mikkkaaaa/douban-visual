import pandas as pd
import streamlit as st
from sqlalchemy import text


def get_conn():
    """
    获取 Streamlit MySQL 数据库连接。
    使用 .streamlit/secrets.toml 中的 connections.mysql 配置。
    """
    return st.connection("mysql", type="sql")


def init_user_library_table():
    """
    初始化用户个人书库表。
    如果 user_books 表不存在，就自动创建。
    """
    conn = get_conn()

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS user_books (
        id INT PRIMARY KEY AUTO_INCREMENT,
        user_id INT NOT NULL,
        title VARCHAR(255) NOT NULL,
        author VARCHAR(255),
        rating FLOAT,
        publish_year INT,
        comment_count INT,
        intro TEXT,
        tags TEXT,
        source_file VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_user_id (user_id)
    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    """

    with conn.session as session:
        session.execute(text(create_table_sql))
        session.commit()


def safe_value(value):
    """
    将 pandas / numpy 中的空值转成 None，避免写入 MySQL 出错。
    同时把 numpy 标量转换成普通 Python 类型。
    """
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    try:
        if hasattr(value, "item"):
            return value.item()
    except Exception:
        pass

    return value


def insert_user_books(user_id, books_df, source_file):
    """
    将用户上传、粘贴或手动录入的书籍数据写入 user_books 表。
    """
    init_user_library_table()

    conn = get_conn()

    insert_sql = """
    INSERT INTO user_books (
        user_id,
        title,
        author,
        rating,
        publish_year,
        comment_count,
        intro,
        tags,
        source_file
    )
    VALUES (
        :user_id,
        :title,
        :author,
        :rating,
        :publish_year,
        :comment_count,
        :intro,
        :tags,
        :source_file
    );
    """

    rows = []

    for _, row in books_df.iterrows():
        title = safe_value(row.get("书名"))

        if title is None or str(title).strip() == "":
            continue

        rows.append({
            "user_id": user_id,
            "title": str(title).strip(),
            "author": safe_value(row.get("作者")),
            "rating": safe_value(row.get("评分")),
            "publish_year": safe_value(row.get("出版年份")),
            "comment_count": safe_value(row.get("评论数")),
            "intro": safe_value(row.get("简介")),
            "tags": safe_value(row.get("标签")),
            "source_file": source_file
        })

    if not rows:
        return 0

    with conn.session as session:
        session.execute(text(insert_sql), rows)
        session.commit()

    return len(rows)


def get_user_books(user_id):
    """
    读取当前登录用户自己的个人书库。
    """
    init_user_library_table()

    conn = get_conn()

    sql = """
    SELECT
        id,
        title AS 书名,
        author AS 作者,
        rating AS 评分,
        publish_year AS 出版年份,
        comment_count AS 评论数,
        intro AS 简介,
        tags AS 标签,
        source_file AS 来源文件,
        created_at AS 添加时间
    FROM user_books
    WHERE user_id = :user_id
    ORDER BY created_at DESC, id DESC;
    """

    with conn.session as session:
        result = session.execute(
            text(sql),
            {"user_id": user_id}
        ).mappings().all()

    return pd.DataFrame([dict(row) for row in result])


def update_user_book(user_id, book_id, book_data):
    """
    修改当前用户个人书库中的一本书。
    注意：WHERE 条件里带 user_id，保证用户只能修改自己的书库数据。
    """
    init_user_library_table()

    conn = get_conn()

    sql = """
    UPDATE user_books
    SET
        title = :title,
        author = :author,
        rating = :rating,
        publish_year = :publish_year,
        comment_count = :comment_count,
        intro = :intro,
        tags = :tags
    WHERE user_id = :user_id AND id = :book_id;
    """

    with conn.session as session:
        result = session.execute(
            text(sql),
            {
                "user_id": user_id,
                "book_id": book_id,
                "title": safe_value(book_data.get("书名")),
                "author": safe_value(book_data.get("作者")),
                "rating": safe_value(book_data.get("评分")),
                "publish_year": safe_value(book_data.get("出版年份")),
                "comment_count": safe_value(book_data.get("评论数")),
                "intro": safe_value(book_data.get("简介")),
                "tags": safe_value(book_data.get("标签")),
            }
        )
        session.commit()

    return result.rowcount


def delete_user_book(user_id, book_id):
    """
    删除当前用户个人书库中的一本书。
    """
    init_user_library_table()

    conn = get_conn()

    sql = """
    DELETE FROM user_books
    WHERE user_id = :user_id AND id = :book_id;
    """

    with conn.session as session:
        result = session.execute(
            text(sql),
            {
                "user_id": user_id,
                "book_id": book_id
            }
        )
        session.commit()

    return result.rowcount


def clear_user_books(user_id):
    """
    清空当前用户的个人书库。
    """
    init_user_library_table()

    conn = get_conn()

    sql = """
    DELETE FROM user_books
    WHERE user_id = :user_id;
    """

    with conn.session as session:
        result = session.execute(
            text(sql),
            {"user_id": user_id}
        )
        session.commit()

    return result.rowcount