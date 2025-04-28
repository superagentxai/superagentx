import datetime
import uuid
from enum import Enum
from pathlib import Path

import aiosqlite

from superagentx.utils.helper import iter_to_aiter


class SQLiteManager:
    """
    A class to manage SQLite database connections.

    This class provides functionality to establish and manage a connection
    to an SQLite database, either in memory or from a file.

    """
    def __init__(
            self,
            db_path: str | Path = ":memory:"
    ):
        self.db_path = db_path
        self.connection: aiosqlite.Connection | None = None
        """
        Parameters:
            db_path : str, optional
                The file path to the SQLite database. Defaults to ":memory:" 
                for an in-memory database.
        """

    async def __aenter__(self):
        self.connection = await aiosqlite.connect(
            database=self.db_path,
            check_same_thread=False
        )
        await self.create_table()
        return self

    async def __aexit__(
            self,
            exc_type,
            exc_val,
            exc_tb
    ):
        await self.connection.close()

    async def create_table(self):
        """
        Asynchronously creates a table in the SQLite database.

        This method will execute an SQL statement to create a table.
        It requires an active database connection and should be
        implemented to define the specific structure of the table
        (e.g., table name and columns).

        Notes:
        ------
        This method is asynchronous, meaning it must be awaited and
        should be run within an asynchronous event loop.
        """
        await self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS history (
                id TEXT PRIMARY KEY,
                memory_id TEXT,
                conversation_id TEXT,
                message_id TEXT,
                created_at DATETIME,
                updated_at DATETIME,
                role TEXT,
                data TEXT,
                reason TEXT,
                is_deleted BOOLEAN
            )
        """
        )

    async def get_history(
            self,
            *,
            memory_id: str,
            conversation_id: str
    ) -> list | None:
        """
        Asynchronously retrieves the chat history for a specific user and chat session.

        Parameters:
            memory_id : str
                The unique identifier of the user whose chat history is being requested.
            conversation_id : str
                The unique identifier of the chat session to retrieve the history from.
        """
        cursor = await self.connection.execute(
            """
            SELECT id, memory_id, conversation_id, message_id, role, data, reason, created_at, updated_at, is_deleted
            FROM history
            WHERE memory_id = ? AND conversation_id = ?
            ORDER BY created_at ASC
        """,
            (memory_id, conversation_id),
        )
        rows = await cursor.fetchall()
        if not rows:
            return None
        return [
            {
                "id": row[0],
                "memory_id": row[1],
                "conversation_id": row[2],
                "message_id": row[3],
                "role": row[4],
                "data": row[5],
                "reason": row[6],
                "created_at": row[7],
                "updated_at": row[8],
                "is_deleted": row[9]
            }
            async for row in iter_to_aiter(rows)
        ]

    async def _get_user_by_id(
            self,
            memory_id: str
    ):
        """
        Asynchronously retrieves user information by user ID.

        This is an internal method intended to query the database for a user
        record matching the provided user ID.

        Parameters:
            memory_id : str
                The unique identifier of the user to be retrieved.

        """
        cursor = await self.connection.execute(
                """
                SELECT id, memory_id, conversation_id, message_id, role, data, reason, created_at, updated_at, is_deleted
                FROM history
                WHERE memory_id = ?
                ORDER BY updated_at ASC
            """,
                (memory_id,),
        )
        return await cursor.fetchall()

    async def reset(self):
        """
        Asynchronously resets the database by dropping the history table.

        This method will execute an SQL query to drop the `history` table if it exists,
        effectively clearing the stored chat history.
        """
        await self.connection.execute("DROP TABLE IF EXISTS history")

    async def add_history(
            self,
            *,
            memory_id: str,
            conversation_id: str,
            message_id: str,
            role: str | Enum,
            data: str,
            reason: str,
            created_at: datetime.datetime | None = None,
            updated_at: datetime.datetime | None = None,
            is_deleted: bool = False,
    ):
        """
        Asynchronously adds a message to the chat history.

        This method stores a new chat message in the database with various
        details, including user and chat session information, message content,
        event type, and timestamps.

        Parameters:
            memory_id : str
                The unique identifier of the user who sent the message.
            conversation_id : str
                The unique identifier of the chat session where the message was sent.
            message_id : str
                A unique identifier for the message being added to the history.
            role : str or Enum
                The role of the user sending the message (e.g., "user", "assistant").
            data : str
                The actual message content to be stored.
            reason: str
                The actual reason content to be stored.
            created_at : datetime, optional
                The timestamp when the message was created. Defaults to the current time if not provided.
            updated_at : datetime, optional
                The timestamp when the message was last updated. Defaults to None.
            is_deleted : bool, optional
                A flag indicating whether the message has been deleted. Defaults to False.
        """
        if not created_at:
            created_at = datetime.datetime.now()
        if not updated_at:
            updated_at = datetime.datetime.now()
        await self.connection.execute(
            """
            INSERT INTO history (id, memory_id, conversation_id, message_id, role, data, reason, created_at, updated_at, is_deleted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                uuid.uuid4().hex,
                memory_id,
                conversation_id,
                message_id,
                role,
                data,
                reason,
                created_at,
                updated_at,
                is_deleted
            ),
        )
        await self.connection.commit()
