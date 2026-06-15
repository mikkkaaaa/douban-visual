import streamlit as st
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from utils.password_utils import hash_password, verify_password


def get_conn():
    """
    获取 Streamlit MySQL 数据库连接。
    使用的是 .streamlit/secrets.toml 里的 connections.mysql 配置。
    """
    return st.connection("mysql", type="sql")


def init_user_tables():
    """
    初始化用户表。
    如果 users 表不存在，就自动创建。
    """
    conn = get_conn()

    create_users_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id INT PRIMARY KEY AUTO_INCREMENT,
        username VARCHAR(50) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
    """

    with conn.session as session:
        session.execute(text(create_users_sql))
        session.commit()


def get_user_by_username(username: str):
    """
    根据用户名查询用户。
    """
    conn = get_conn()

    sql = """
    SELECT id, username, password_hash, created_at
    FROM users
    WHERE username = :username
    LIMIT 1;
    """

    with conn.session as session:
        result = session.execute(
            text(sql),
            {"username": username}
        ).mappings().first()

    if result:
        return dict(result)

    return None


def create_user(username: str, password: str):
    """
    创建新用户。
    返回：
    True, "注册成功"
    False, "失败原因"
    """
    username = username.strip()

    if not username:
        return False, "用户名不能为空"

    if len(username) < 3:
        return False, "用户名至少需要 3 个字符"

    if len(password) < 6:
        return False, "密码至少需要 6 位"

    password_hash = hash_password(password)

    conn = get_conn()

    sql = """
    INSERT INTO users (username, password_hash)
    VALUES (:username, :password_hash);
    """

    try:
        with conn.session as session:
            session.execute(
                text(sql),
                {
                    "username": username,
                    "password_hash": password_hash
                }
            )
            session.commit()

        return True, "注册成功，请登录"

    except IntegrityError:
        return False, "用户名已存在"

    except Exception as e:
        return False, f"注册失败：{e}"


def login_user(username: str, password: str):
    """
    登录验证。
    返回：
    True, user_dict
    False, error_message
    """
    username = username.strip()

    if not username or not password:
        return False, "请输入用户名和密码"

    user = get_user_by_username(username)

    if not user:
        return False, "用户不存在"

    if not verify_password(password, user["password_hash"]):
        return False, "密码错误"

    login_user_info = {
        "id": user["id"],
        "username": user["username"]
    }

    return True, login_user_info