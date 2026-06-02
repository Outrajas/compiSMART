import sqlite3
import os
from app.core.logger import logger

# Support dynamic database URL for future Postgres deployment compatibility
DB_PATH = os.getenv("DATABASE_URL", "metadata.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()

    # =========================
    # Videos / Reels Table
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
            hook_text TEXT,
            follower_count INTEGER DEFAULT 0,
            following_count INTEGER DEFAULT 0,
            posts_count INTEGER DEFAULT 0,
            bio TEXT,
            transcript TEXT,
            engagement_rate REAL DEFAULT 0,
            views_per_follower REAL DEFAULT 0,
            hook_score REAL DEFAULT 0,
            transcript_coverage REAL DEFAULT 0,
            question_count INTEGER DEFAULT 0,
            emotion_words INTEGER DEFAULT 0,
            conflict_score INTEGER DEFAULT 0,
            humor_score INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # =========================
    # Automatic Migration Check
    # =========================
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(videos)")
    columns = [row["name"] for row in cursor.fetchall()]
    
    migrations = {
        "hook_text": "ALTER TABLE videos ADD COLUMN hook_text TEXT",
        "following_count": "ALTER TABLE videos ADD COLUMN following_count INTEGER DEFAULT 0",
        "posts_count": "ALTER TABLE videos ADD COLUMN posts_count INTEGER DEFAULT 0",
        "bio": "ALTER TABLE videos ADD COLUMN bio TEXT",
        "question_count": "ALTER TABLE videos ADD COLUMN question_count INTEGER DEFAULT 0",
        "emotion_words": "ALTER TABLE videos ADD COLUMN emotion_words INTEGER DEFAULT 0",
        "conflict_score": "ALTER TABLE videos ADD COLUMN conflict_score INTEGER DEFAULT 0",
        "humor_score": "ALTER TABLE videos ADD COLUMN humor_score INTEGER DEFAULT 0"
    }

    for col, query in migrations.items():
        if col not in columns:
            logger.info(f"Migrating database: Adding '{col}' column to 'videos' table.")
            try:
                conn.execute(query)
                conn.commit()
                logger.info(f"Migration successful: '{col}' column added.")
            except Exception as e:
                logger.error(f"Migration failed for column {col}: {e}")

    # =========================
    # Datasets (Isolation Layer)
    # =========================
    conn.execute("""
        CREATE TABLE IF NOT EXISTS datasets (
            dataset_id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS dataset_videos (
            dataset_id TEXT NOT NULL,
            video_id TEXT NOT NULL,
            PRIMARY KEY (dataset_id, video_id)
        )
    """)

    # =========================
    # Schema Auto-Healing for Caches
    # =========================
    # If older versions of these cache tables exist on disk with mismatched columns,
    # drop them safely so they can be recreated cleanly below.
    cursor.execute("PRAGMA table_info(dataset_analytics)")
    da_cols = [r["name"] for r in cursor.fetchall()]
    if da_cols and "dataset_hash" not in da_cols:
        conn.execute("DROP TABLE dataset_analytics")

    cursor.execute("PRAGMA table_info(answer_cache)")
    ac_cols = [r["name"] for r in cursor.fetchall()]
    if ac_cols and "sources_json" not in ac_cols:
        conn.execute("DROP TABLE answer_cache")

    cursor.execute("PRAGMA table_info(video_semantic_cache)")
    vsc_cols = [r["name"] for r in cursor.fetchall()]
    if vsc_cols and "semantic_profile_json" not in vsc_cols:
        conn.execute("DROP TABLE video_semantic_cache")

    # =========================
    # Analytics Database Caching 
    # =========================
    conn.execute("""
        CREATE TABLE IF NOT EXISTS dataset_analytics (
            dataset_id TEXT,
            dataset_hash TEXT,
            summary_json TEXT,
            rankings_json TEXT,
            semantic_profiles_json TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (dataset_id, dataset_hash)
        )
    """)

    # =========================
    # LLM Answer Cache
    # =========================
    conn.execute("""
        CREATE TABLE IF NOT EXISTS answer_cache (
            dataset_id TEXT,
            question_hash TEXT,
            answer TEXT,
            sources_json TEXT,
            model_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(dataset_id, question_hash)
        )
    """)

    # =========================
    # Semantic Profiles Cache
    # =========================
    conn.execute("""
        CREATE TABLE IF NOT EXISTS video_semantic_cache (
            video_id TEXT PRIMARY KEY,
            semantic_profile_json TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # =========================
    # Chat & Session Memory
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

# --- CACHE OPERATIONS ---
def get_dataset_analytics_cache(dataset_id: str, dataset_hash: str):
    conn = get_connection()
    row = conn.execute("SELECT * FROM dataset_analytics WHERE dataset_id = ? AND dataset_hash = ?", (dataset_id, dataset_hash)).fetchone()
    conn.close()
    return dict(row) if row else None

def set_dataset_analytics_cache(dataset_id: str, dataset_hash: str, summary: str, rankings: str, profiles: str):
    conn = get_connection()
    conn.execute("""
        INSERT OR REPLACE INTO dataset_analytics (dataset_id, dataset_hash, summary_json, rankings_json, semantic_profiles_json, updated_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (dataset_id, dataset_hash, summary, rankings, profiles))
    conn.commit()
    conn.close()

def get_answer_cache(dataset_id: str, question_hash: str):
    conn = get_connection()
    row = conn.execute("SELECT * FROM answer_cache WHERE dataset_id = ? AND question_hash = ?", (dataset_id, question_hash)).fetchone()
    conn.close()
    return dict(row) if row else None

def set_answer_cache(dataset_id: str, question_hash: str, answer: str, sources_json: str, model_name: str):
    conn = get_connection()
    conn.execute("""
        INSERT OR REPLACE INTO answer_cache (dataset_id, question_hash, answer, sources_json, model_name, created_at)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (dataset_id, question_hash, answer, sources_json, model_name))
    conn.commit()
    conn.close()

def get_video_semantic_cache(video_id: str):
    conn = get_connection()
    row = conn.execute("SELECT semantic_profile_json FROM video_semantic_cache WHERE video_id = ?", (video_id,)).fetchone()
    conn.close()
    return row["semantic_profile_json"] if row else None

def set_video_semantic_cache(video_id: str, semantic_profile_json: str):
    conn = get_connection()
    conn.execute("""
        INSERT OR REPLACE INTO video_semantic_cache (video_id, semantic_profile_json, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
    """, (video_id, semantic_profile_json))
    conn.commit()
    conn.close()

# --- EXISTING LINKS ---
def add_video_to_dataset(dataset_id: str, video_id: str):
    conn = get_connection()
    conn.execute("INSERT OR IGNORE INTO dataset_videos (dataset_id, video_id) VALUES (?, ?)", (dataset_id, video_id))
    conn.commit()
    conn.close()

def remove_video_from_dataset(dataset_id: str, video_id: str):
    conn = get_connection()
    conn.execute("DELETE FROM dataset_videos WHERE dataset_id = ? AND video_id = ?", (dataset_id, video_id))
    conn.commit()
    conn.close()

def get_dataset_video_ids(dataset_id: str) -> list[str]:
    conn = get_connection()
    rows = conn.execute("SELECT video_id FROM dataset_videos WHERE dataset_id = ?", (dataset_id,)).fetchall()
    conn.close()
    return [row["video_id"] for row in rows]

def add_chat_message(session_id: str, role: str, content: str):
    conn = get_connection()
    conn.execute("INSERT INTO chat_messages (session_id, role, content) VALUES (?, ?, ?)", (session_id, role, content))
    conn.commit()
    conn.close()

def get_chat_history(session_id: str, limit: int = 20) -> str:
    conn = get_connection()
    rows = conn.execute("SELECT role, content FROM chat_messages WHERE session_id = ? ORDER BY timestamp ASC LIMIT ?", (session_id, limit)).fetchall()
    conn.close()
    history = []
    for row in rows:
        history.append(f"User: {row['content']}" if row["role"] == "user" else f"Assistant: {row['content']}")
    return "\n".join(history)