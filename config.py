import os
import secrets

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

    # MySQL 配置 - 修改这里切换数据库
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = os.environ.get('MYSQL_PORT', '3306')
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASS = os.environ.get('MYSQL_PASS', '')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'hotel_dark')

    # 数据库连接：优先DATABASE_URL，回退MySQL，再回退SQLite
    raw_uri = os.environ.get("DATABASE_URL")
    if raw_uri:
        # Railway 提供 postgres:// 需要替换为 postgresql://
        if raw_uri.startswith("postgres://"):
            raw_uri = raw_uri.replace("postgres://", "postgresql://", 1)
        SQLALCHEMY_DATABASE_URI = raw_uri
    elif MYSQL_PASS or os.environ.get('USE_MYSQL'):
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASS}"
            f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4"
        )
    else:
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(BASE_DIR, "hotel.db")}'

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = os.environ.get('FLASK_DEBUG', '1') == '1'
    PER_PAGE = 12
