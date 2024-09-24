import datetime
import uuid
from enum import Enum
from pathlib import Path

import aiosqlite

from agentx.utils.helper import iter_to_aiter


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

    async def get_history(
            self,
            user_id: str,
            chat_id: str
    ):
        """
        Asynchronously retrieves the chat history for a specific user and chat session.

        Parameters:
            user_id : str
                The unique identifier of the user whose chat history is being requested.
            chat_id : str
                The unique identifier of the chat session to retrieve the history from.
        """
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

    async def _get_user_by_id(
            self,
            user_id: str
    ):
        """
        Asynchronously retrieves user information by user ID.

        This is an internal method intended to query the database for a user
        record matching the provided user ID.

        Parameters:
            user_id : str
                The unique identifier of the user to be retrieved.

        """
        cursor = await self.connection.execute(
                """
                SELECT id, user_id, chat_id, message_id, event, role, message, created_at, updated_at, is_deleted
                FROM history
                WHERE user_id = ?
                ORDER BY updated_at ASC
            """,
                (user_id,),
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
            user_id: str,
            chat_id: str,
            message_id: str,
            event: str,
            role: str | Enum,
            message: str,
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
            user_id : str
                The unique identifier of the user who sent the message.
            chat_id : str
                The unique identifier of the chat session where the message was sent.
            message_id : str
                A unique identifier for the message being added to the history.
            event : str
                The type of event (e.g., "ADD", "UPDATE").
            role : str or Enum
                The role of the user sending the message (e.g., "user", "assistant").
            message : str
                The actual message content to be stored.
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
