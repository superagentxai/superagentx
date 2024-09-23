import uuid
import uuid

import aiosqlite
from aiosqlite import Connection

from agentx.utils.helper import iter_to_aiter


class SQLiteManager:
    def __init__(self, db_path=":memory:"):
        self.db_path = db_path

    async def _connection(self) -> Connection:
        connection = await aiosqlite.connect(self.db_path, check_same_thread=False)
        return connection

    async def create_table(self):
        connection = await self._connection()
        try:
            await connection.execute(
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
        finally:
            await connection.close()

    async def get_history(self, user_id, chat_id):
        connection = await self._connection()
        try:
            cursor = await connection.execute(
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
        finally:
            await connection.close()

    async def _get_user_by_id(self, user_id):
        connection = await self._connection()
        try:
            cursor = await connection.execute(
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
        finally:
            await connection.close()

    async def reset(self):
        connection = await self._connection()
        try:
            await connection.execute("DROP TABLE IF EXISTS history")
        finally:
            await connection.close()

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
        connection = await self._connection()
        try:
            await connection.execute(
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
            await connection.commit()
        finally:
            await connection.close()
