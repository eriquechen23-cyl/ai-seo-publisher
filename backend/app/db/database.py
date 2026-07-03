import sqlite3
from pathlib import Path


def database_path_from_url(database_url: str) -> Path:
    if not database_url.startswith("sqlite:///"):
        raise ValueError("Only sqlite:/// database URLs are supported in this demo")

    raw_path = database_url.replace("sqlite:///", "", 1)
    path = Path(raw_path)
    return path


def connect(database_url: str) -> sqlite3.Connection:
    path = database_path_from_url(database_url)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_bytes(b"")
    connection = sqlite3.connect(path)
    connection.execute("PRAGMA journal_mode=OFF")
    connection.row_factory = sqlite3.Row
    return connection


def init_db(database_url: str) -> None:
    with connect(database_url) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS article_jobs (
                id TEXT PRIMARY KEY,
                topic TEXT NOT NULL,
                keywords_json TEXT NOT NULL,
                target_audience TEXT NOT NULL,
                call_to_action TEXT NOT NULL,
                generated_title TEXT,
                generated_html TEXT,
                status TEXT NOT NULL,
                wordpress_post_id INTEGER,
                error_code TEXT,
                error_message TEXT,
                reflection_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.commit()
