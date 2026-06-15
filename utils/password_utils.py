import os
import hashlib
import hmac


def hash_password(password: str) -> str:
    """
    使用 PBKDF2 对密码进行加密。
    返回格式：salt:hash
    """
    salt = os.urandom(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100000
    )

    return salt.hex() + ":" + password_hash.hex()


def verify_password(password: str, stored_hash: str) -> bool:
    """
    验证用户输入的密码是否和数据库中的加密密码一致。
    """
    try:
        salt_hex, hash_hex = stored_hash.split(":")
        salt = bytes.fromhex(salt_hex)

        new_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            100000
        )

        return hmac.compare_digest(new_hash.hex(), hash_hex)

    except Exception:
        return False