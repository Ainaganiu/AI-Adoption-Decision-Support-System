from __future__ import annotations

"""MySQL setup utilities."""

from typing import Generator
from urllib.parse import unquote, urlparse

import pymysql
from pymysql.connections import Connection
from pymysql.cursors import DictCursor

from .config import get_settings

settings = get_settings()


def _parse_mysql_uri(uri: str) -> dict[str, str | int]:
    parsed = urlparse(uri)
    if parsed.scheme not in {"mysql", "mysql+pymysql"}:
        raise ValueError("Unsupported MySQL DSN scheme.")
    if not parsed.hostname or not parsed.path:
        raise ValueError("MySQL DSN must include host and database name.")
    return {
        "host": parsed.hostname,
        "port": parsed.port or 3306,
        "user": unquote(parsed.username or ""),
        "password": unquote(parsed.password or ""),
        "database": parsed.path.lstrip("/"),
    }


def _connection_params() -> dict[str, str | int]:
    if settings.mysql_uri:
        return _parse_mysql_uri(settings.mysql_uri)
    return {
        "host": settings.mysql_host,
        "port": settings.mysql_port,
        "user": settings.mysql_user,
        "password": settings.mysql_password or "",
        "database": settings.mysql_db,
    }


def _make_connection() -> Connection:
    return pymysql.connect(
        **_connection_params(),
        cursorclass=DictCursor,
        autocommit=True,
        connect_timeout=5,
    )


def _make_server_connection() -> Connection:
    params = dict(_connection_params())
    params.pop("database", None)
    return pymysql.connect(
        **params,
        cursorclass=DictCursor,
        autocommit=True,
        connect_timeout=5,
    )


def _quote_identifier(value: str) -> str:
    safe = value.replace("`", "``")
    return f"`{safe}`"


def _ensure_database(db_name: str) -> None:
    if not db_name:
        raise ValueError("MySQL database name missing. Set DSS_MYSQL_DB or DSS_MYSQL_URI.")
    conn = _make_server_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {_quote_identifier(db_name)}")
    finally:
        conn.close()


def _ensure_tables(conn: Connection) -> None:
    create_table_sql = """
        CREATE TABLE IF NOT EXISTS `survey_submission_responses` (
            `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
            `created_at` DATETIME NOT NULL,
            `profession` VARCHAR(120) NOT NULL,
            `years_in_profession` TINYINT NOT NULL,
            `is_familiar_with_ai` TINYINT NOT NULL,
            `openness_to_ai` VARCHAR(32) NOT NULL,
            `ai_tasks` TEXT NOT NULL,
            `ai_tasks_other` TEXT NULL,
            `concerns` TEXT NOT NULL,
            `job_replacement_concern` VARCHAR(32) NOT NULL,
            `expected_benefits` TEXT NOT NULL,
            `safeguards_needed` TEXT NOT NULL,
            `safeguards_notes` TEXT NULL,
            `wants_recommendation` TINYINT NOT NULL,
            `email` VARCHAR(255) NULL,
            `additional_notes` TEXT NULL,
            `raw_payload` LONGTEXT NOT NULL,
            `recommendation` LONGTEXT NULL,
            `readiness_score` INT NOT NULL,
            INDEX `idx_survey_created_at` (`created_at`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """
    with conn.cursor() as cursor:
        cursor.execute(create_table_sql)
        cursor.execute(
            "SHOW COLUMNS FROM `survey_submission_responses` LIKE 'recommendation'"
        )
        if not cursor.fetchone():
            cursor.execute(
                "ALTER TABLE `survey_submission_responses` "
                "ADD COLUMN `recommendation` LONGTEXT NULL"
            )


def get_db() -> Generator[Connection, None, None]:
    """FastAPI dependency that yields a `pymysql` connection."""

    conn = _make_connection()
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    """Ensure the MySQL connection is healthy."""

    db_name = _connection_params().get("database")
    _ensure_database(str(db_name or ""))
    conn = _make_connection()
    try:
        _ensure_tables(conn)
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
    finally:
        conn.close()
