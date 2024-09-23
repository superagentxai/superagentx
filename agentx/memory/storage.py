import uuid

import aiosqlite
from aiosqlite import Connection

from agentx.utils.helper import iter_to_aiter


class SQLiteManager:
    def __init__(self, db_path=":memory:"):
        self.db_path = db_path
        self.connection = None

    async def __aenter__(self):
        self.connection = await aiosqlite.connect(self.db_path, check_same_thread=False)
        await self.create_table()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.connection.close()

    async def create_table(self):
        await self.connection.execute(
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

    async def get_history(self, user_id, chat_id):
        cursor = await self.connection.execute(
            """
            SELECT id, user_id, chat_id, message_id, event, role, message, created_at, updated_at, is_deleted
            FROM history
            WHERE user_id = ? AND chat_id = ?
            ORDER BY created_at ASC
        """,
            (user_id, chat_id),
        )
        rows = await cursor.fetchall()
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
                async for row in iter_to_aiter(rows)
            ]

    async def _get_user_by_id(self, user_id):
        cursor = await self.connection.execute(
                """
                SELECT id, user_id, chat_id, message_id, event, role, message, created_at, updated_at, is_deleted
                FROM history
                WHERE user_id = ?
                ORDER BY updated_at ASC
            """,
                (user_id,),
        )
        rows = await cursor.fetchall()
        if rows:
            return rows

    async def reset(self):
        await self.connection.execute("DROP TABLE IF EXISTS history")

    async def add_history(
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
        await self.connection.execute(
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
        await self.connection.commit()
