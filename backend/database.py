import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "study.db"


def get_connection():
    """连接到 SQLite 数据库，并让查询结果可以像字典一样读取。"""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def execute_query(sql, params=()):
    """执行查询语句，返回由 dict 组成的列表。"""
    with get_connection() as connection:
        cursor = connection.execute(sql, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def execute_update(sql, params=()):
    """执行新增、修改、删除语句，返回受影响行数。"""
    with get_connection() as connection:
        cursor = connection.execute(sql, params)
        connection.commit()
        return cursor.rowcount
