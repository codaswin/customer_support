import sqlite3
import uuid


class Store:
    """Durable Support Threads in SQLite."""

    def __init__(self, path):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS threads (
                id TEXT PRIMARY KEY, name TEXT, email TEXT, specialist TEXT);
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT, sender TEXT, text TEXT);
            """
        )

    def create_thread(self, name, email, specialist):
        thread_id = uuid.uuid4().hex
        with self.db:
            self.db.execute(
                "INSERT INTO threads VALUES (?, ?, ?, ?)", (thread_id, name, email, specialist)
            )
        return thread_id

    def add_message(self, thread_id, sender, text):
        with self.db:
            self.db.execute(
                "INSERT INTO messages (thread_id, sender, text) VALUES (?, ?, ?)",
                (thread_id, sender, text),
            )

    def get_thread(self, thread_id):
        row = self.db.execute(
            "SELECT specialist FROM threads WHERE id = ?", (thread_id,)
        ).fetchone()
        if row is None:
            return None
        msgs = self.db.execute(
            "SELECT sender, text FROM messages WHERE thread_id = ? ORDER BY id", (thread_id,)
        ).fetchall()
        return {
            "thread_id": thread_id,
            "specialist": row[0],
            "messages": [{"sender": s, "text": t} for s, t in msgs],
        }
