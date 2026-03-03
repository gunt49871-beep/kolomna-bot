import json
import aiosqlite
from datetime import datetime, timezone

DB_PATH = "bot.db"
MAX_HISTORY = 20


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_states (
                user_id TEXT PRIMARY KEY,
                state_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        await db.commit()


def _default_state() -> dict:
    return {
        "history": [],
        "failed_attempts": 0,
        "appeal_step": None,
        "appeal_data": {
            "name": None,
            "phone": None,
            "topic": None,
            "description": None,
        },
    }


async def get_state(user_id: str) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT state_json FROM user_states WHERE user_id = ?", (str(user_id),)
        ) as cursor:
            row = await cursor.fetchone()
    if row:
        return json.loads(row[0])
    return _default_state()


async def save_state(user_id: str, state: dict):
    state_json = json.dumps(state, ensure_ascii=False)
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO user_states (user_id, state_json, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET state_json = excluded.state_json, updated_at = excluded.updated_at
            """,
            (str(user_id), state_json, now),
        )
        await db.commit()


async def reset_state(user_id: str):
    await save_state(user_id, _default_state())


def add_to_history(state: dict, role: str, content: str):
    state["history"].append({"role": role, "content": content})
    if len(state["history"]) > MAX_HISTORY:
        state["history"] = state["history"][-MAX_HISTORY:]
