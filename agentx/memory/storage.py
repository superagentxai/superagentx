import sqlite3
import uuid


class SQLiteManager:
    def __init__(self, db_path=":memory:"):
        self.connection = sqlite3.connect(db_path, check_same_thread=False)
        self._create_history_table()

    def _create_history_table(self):
        with self.connection:
            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS history (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    chat_id TEXT,
                    message_id TEXT,
                    created_at DATETIME,
                    updated_at DATETIME,
                    role TEXT,
                    message TEXT,
                    event TEXT,
                    is_deleted BOOLEAN
                )
            """
            )

    def add_history(
            self,
            user_id,
            chat_id,
            message_id,
            event,
            role,
            message,
            created_at=None,
            updated_at=None,
            is_deleted=False,
    ):
        with self.connection:
            self.connection.execute(
                """
                INSERT INTO history (id, user_id, chat_id, message_id, event, role, message, created_at, updated_at, is_deleted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    str(uuid.uuid4()),
                    user_id,
                    chat_id,
                    message_id,
                    event,
                    role,
                    message,
                    created_at,
                    updated_at,
                    is_deleted
                ),
            )

    def get_history(self, user_id, chat_id):
        cursor = self.connection.execute(
            """
            SELECT id, user_id, chat_id, message_id, event, role, message, created_at, updated_at, is_deleted
            FROM history
            WHERE user_id = ? AND chat_id = ?
            ORDER BY created_at ASC
        """,
            (user_id, chat_id),
        )
        rows = cursor.fetchall()
        if rows:
            return [
                {
                    "id": row[0],
                    "user_id": row[1],
                    "chat_id": row[2],
                    "message_id": row[3],
                    "event": row[4],
                    "role": row[5],
                    "message": row[6],
                    "created_at": row[7],
                    "updated_at": row[8],
                    "is_deleted": row[9]
                }
                for row in rows
            ]

    def _get_user_by_id(self, user_id):
        cursor = self.connection.execute(
            """
            SELECT id, user_id, chat_id, message_id, event, role, message, created_at, updated_at, is_deleted
            FROM history
            WHERE user_id = ?
            ORDER BY updated_at ASC
        """,
            (user_id,),
        )
        rows = cursor.fetchall()
        if rows:
            return rows

    def reset(self):
        with self.connection:
            self.connection.execute("DROP TABLE IF EXISTS history")
