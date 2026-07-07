"""SQLite database layer for kaljuvee.chat (Talk to Julian).

Small, single-file SQLite DB holding only chat auth + history: users, sessions,
messages. `SCHEMA = "main"` is SQLite's default database name, so schema-qualified
queries like `main.chat_users` used elsewhere remain valid.
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.pool import StaticPool

load_dotenv()

# Default to a local SQLite file; override with DB_URL for other setups.
DB_URL = os.environ.get("DB_URL", "sqlite:///kaljuvee_chat.db")
SCHEMA = "main"  # SQLite's default database name

_is_sqlite = DB_URL.startswith("sqlite")

if _is_sqlite:
    engine = create_engine(
        DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool if ":memory:" in DB_URL else None,
        pool_pre_ping=True,
    )
else:  # pragma: no cover - kept for optional Postgres deploys
    engine = create_engine(DB_URL, pool_pre_ping=True, pool_size=5, max_overflow=10)


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create the chat tables if they don't exist."""
    ddl = [
        """CREATE TABLE IF NOT EXISTS chat_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255),
            name VARCHAR(200),
            is_verified BOOLEAN DEFAULT 0,
            verify_token VARCHAR(64),
            reset_token VARCHAR(64),
            reset_token_expires TIMESTAMP,
            role VARCHAR(20) DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES chat_users(id),
            title VARCHAR(255) DEFAULT 'New chat',
            agent_slug VARCHAR(100),
            share_token VARCHAR(64),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER REFERENCES chat_sessions(id),
            role VARCHAR(20) NOT NULL,
            content TEXT NOT NULL,
            agent_slug VARCHAR(100),
            tool_calls TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
    ]
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_chat_sessions_user ON chat_sessions(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id)",
    ]
    with engine.connect() as conn:
        for stmt in ddl:
            conn.execute(text(stmt))
        for stmt in indexes:
            conn.execute(text(stmt))
        conn.commit()
