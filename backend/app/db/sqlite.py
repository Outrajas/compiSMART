import sqlite3
from app.core.logger import logger

DB_PATH = "metadata.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()

    # =========================
    # Videos
    # =========================
    conn.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            video_id TEXT PRIMARY KEY,
            youtube_id TEXT UNIQUE,
            dataset_id TEXT,

            platform TEXT NOT NULL,
            title TEXT,
            creator TEXT,

            views INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            comments INTEGER DEFAULT 0,

            duration INTEGER DEFAULT 0,
            upload_date TEXT,
            hashtags TEXT,

            follower_count INTEGER DEFAULT 0,

            transcript TEXT,

            engagement_rate REAL DEFAULT 0,
            views_per_follower REAL DEFAULT 0,
            hook_score REAL DEFAULT 0,
            transcript_coverage REAL DEFAULT 0,

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # =========================
    # Datasets
    # =========================
    conn.execute("""
        CREATE TABLE IF NOT EXISTS datasets (
            dataset_id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # =========================
    # Dataset ↔ Video Links
    # =========================
    conn.execute("""
        CREATE TABLE IF NOT EXISTS dataset_videos (
            dataset_id TEXT NOT NULL,
            video_id TEXT NOT NULL,

            PRIMARY KEY (dataset_id, video_id)
        )
    """)

    # =========================
    # Chat Messages
    # =========================
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # =========================
    # Session State
    # =========================
    conn.execute("""
        CREATE TABLE IF NOT EXISTS session_state (
            session_id TEXT PRIMARY KEY,
            last_intent TEXT,
            last_topic TEXT,
            active_videos TEXT,
            last_comparison TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

    logger.info("Database initialized successfully")


def add_chat_message(session_id: str, role: str, content: str):
    conn = get_connection()

    conn.execute(
        """
        INSERT INTO chat_messages
        (session_id, role, content)
        VALUES (?, ?, ?)
        """,
        (session_id, role, content)
    )

    conn.commit()
    conn.close()


def get_chat_history(session_id: str, limit: int = 20) -> str:
    conn = get_connection()

    rows = conn.execute(
        """
        SELECT role, content
        FROM chat_messages
        WHERE session_id = ?
        ORDER BY timestamp ASC
        LIMIT ?
        """,
        (session_id, limit)
    ).fetchall()

    conn.close()

    history = []

    for row in rows:
        if row["role"] == "user":
            history.append(f"User: {row['content']}")
        else:
            history.append(f"Assistant: {row['content']}")

    return "\n".join(history)


if __name__ == "__main__":
    init_db()
    print("Database created successfully.")
