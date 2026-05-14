"""Repository base class for SQLite data access."""

import sqlite3


class Repository:
    """Base class for database repositories.

    Provides common database operations with proper connection management
    and sqlite3.Row as the row factory for dict-like access to columns.
    """

    def __init__(self, db_path: str):
        """Initialize the repository with a database connection.

        Args:
            db_path: Path to the SQLite database file.
        """
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def execute(self, sql: str, params: tuple = ()) -> None:
        """Execute a SQL statement that does not return results.

        Args:
            sql: The SQL statement to execute.
            params: Parameters to bind to the SQL statement.

        Note:
            Uses context manager to handle transaction commit/rollback.
        """
        with self.conn:
            self.conn.execute(sql, params)

    def query(self, sql: str, params: tuple = ()) -> list:
        """Execute a SELECT statement and return all matching rows.

        Args:
            sql: The SQL SELECT statement to execute.
            params: Parameters to bind to the SQL statement.

        Returns:
            A list of sqlite3.Row objects matching the query.
        """
        cursor = self.conn.execute(sql, params)
        return cursor.fetchall()

    def query_one(self, sql: str, params: tuple = ()) -> sqlite3.Row | None:
        """Execute a SELECT statement and return a single row.

        Args:
            sql: The SQL SELECT statement to execute.
            params: Parameters to bind to the SQL statement.

        Returns:
            The first sqlite3.Row matching the query, or None if no match.
        """
        cursor = self.conn.execute(sql, params)
        return cursor.fetchone()

    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
