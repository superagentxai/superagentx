import sqlite3
import uuid


class SQLiteManager:
    def __init__(self, db_path=":memory:"):
        self.connection = sqlite3.connect(db_path, check_same_thread=False)
        # self._migrate_history_table()
        self._create_history_table()

    # def _migrate_history_table(self):
    #     with self.connection:
    #         cursor = self.connection.cursor()
    #
    #         cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='history'")
    #         table_exists = cursor.fetchone() is not None
    #
    #         if table_exists:
    #             # Get the current schema of the history table
    #             cursor.execute("PRAGMA table_info(history)")
    #             current_schema = {row[1]: row[2] for row in cursor.fetchall()}
    #
    #             # Define the expected schema
    #             expected_schema = {
    #                 "id": "TEXT",
    #                 "memory_id": "TEXT",
    #                 "old_memory": "TEXT",
    #                 "new_memory": "TEXT",
    #                 "new_value": "TEXT",
    #                 "event": "TEXT",
    #                 "created_at": "DATETIME",
    #                 "updated_at": "DATETIME",
    #                 "is_deleted": "INTEGER",
    #             }
    #
    #             # Check if the schemas are the same
    #             if current_schema != expected_schema:
    #                 # Rename the old table
    #                 cursor.execute("ALTER TABLE history RENAME TO old_history")
    #
    #                 cursor.execute(
    #                     """
    #                     CREATE TABLE IF NOT EXISTS history (
    #                         id TEXT PRIMARY KEY,
    #                         memory_id TEXT,
    #                         old_memory TEXT,
    #                         new_memory TEXT,
    #                         new_value TEXT,
    #                         event TEXT,
    #                         created_at DATETIME,
    #                         updated_at DATETIME,
    #                         is_deleted INTEGER
    #                     )
    #                 """
    #                 )
    #
    #                 # Copy data from the old table to the new table
    #                 cursor.execute(
    #                     """
    #                     INSERT INTO history (id, memory_id, old_memory, new_memory, new_value, event, created_at, updated_at, is_deleted)
    #                     SELECT id, memory_id, prev_value, new_value, new_value, event, timestamp, timestamp, is_deleted
    #                     FROM old_history
    #                 """  # noqa: E501
    #                 )
    #
    #                 cursor.execute("DROP TABLE old_history")
    #
    #                 self.connection.commit()

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
            WHERE user_id = ? AND chat_id ?
            ORDER BY updated_at ASC
        """,
            (user_id, chat_id),
        )
        rows = cursor.fetchall()
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
        return rows

    def reset(self):
        with self.connection:
            self.connection.execute("DROP TABLE IF EXISTS history")
