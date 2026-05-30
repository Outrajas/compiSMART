import sqlite3
from app.core.logger import logger

DB_PATH = "metadata.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            video_id TEXT PRIMARY KEY,
            platform TEXT NOT NULL,
            title TEXT,
            creator TEXT,
            views INTEGER,
            likes INTEGER,
            comments INTEGER,
            duration INTEGER,
            upload_date TEXT,
            hashtags TEXT,
            follower_count INTEGER
        )
    """)
    # Add dataset_id column if it doesn't exist
    try:
        conn.execute("ALTER TABLE videos ADD COLUMN dataset_id TEXT")
    except sqlite3.OperationalError:
        pass  # column already exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    logger.info("Database initialized (metadata.db)")

def add_chat_message(session_id: str, role: str, message: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO chat_history (session_id, role, message) VALUES (?, ?, ?)",
        (session_id, role, message)
    )
    conn.commit()
    conn.close()

def get_chat_history(session_id: str, limit: int = 10) -> str:
    conn = get_connection()
    rows = conn.execute(
        "SELECT role, message FROM chat_history WHERE session_id = ? ORDER BY timestamp ASC LIMIT ?",
        (session_id, limit)
    ).fetchall()
    conn.close()
    history = ""
    for row in rows:
        if row["role"] == "user":
            history += f"User: {row['message']}\n"
        else:
            history += f"Assistant: {row['message']}\n"
    return history.strip()