"""Tests for Repository base class."""

import os
import sqlite3
import tempfile
import pytest

from models.repository import Repository


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    os.unlink(path)


@pytest.fixture
def repository(temp_db):
    """Create a Repository instance for testing."""
    repo = Repository(temp_db)
    yield repo
    repo.close()


class TestRepository:
    """Test cases for Repository class."""

    def test_init_creates_connection(self, temp_db):
        """Test that __init__ creates a database connection."""
        repo = Repository(temp_db)
        assert repo.conn is not None
        assert isinstance(repo.conn, sqlite3.Connection)
        repo.close()

    def test_init_sets_row_factory(self, temp_db):
        """Test that __init__ sets row_factory to sqlite3.Row."""
        repo = Repository(temp_db)
        assert repo.conn.row_factory == sqlite3.Row
        repo.close()

    def test_execute_insert(self, repository):
        """Test execute method with INSERT statement."""
        repository.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
        repository.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))

        result = repository.query("SELECT * FROM users")
        assert len(result) == 1
        assert result[0]["name"] == "Alice"

    def test_execute_update(self, repository):
        """Test execute method with UPDATE statement."""
        repository.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
        repository.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))
        repository.execute("UPDATE users SET name = ? WHERE id = ?", ("Bob", 1))

        result = repository.query("SELECT name FROM users WHERE id = 1")
        assert result[0]["name"] == "Bob"

    def test_execute_delete(self, repository):
        """Test execute method with DELETE statement."""
        repository.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
        repository.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))
        repository.execute("DELETE FROM users WHERE id = ?", (1,))

        result = repository.query("SELECT * FROM users")
        assert len(result) == 0

    def test_query_returns_all_rows(self, repository):
        """Test query method returns all matching rows."""
        repository.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
        repository.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))
        repository.execute("INSERT INTO users (name) VALUES (?)", ("Bob",))
        repository.execute("INSERT INTO users (name) VALUES (?)", ("Charlie",))

        result = repository.query("SELECT * FROM users ORDER BY id")
        assert len(result) == 3
        assert result[0]["name"] == "Alice"
        assert result[1]["name"] == "Bob"
        assert result[2]["name"] == "Charlie"

    def test_query_with_params(self, repository):
        """Test query method with parameters."""
        repository.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
        repository.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))
        repository.execute("INSERT INTO users (name) VALUES (?)", ("Bob",))

        result = repository.query("SELECT * FROM users WHERE name = ?", ("Bob",))
        assert len(result) == 1
        assert result[0]["name"] == "Bob"

    def test_query_one_returns_single_row(self, repository):
        """Test query_one method returns a single row."""
        repository.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
        repository.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))
        repository.execute("INSERT INTO users (name) VALUES (?)", ("Bob",))

        result = repository.query_one("SELECT * FROM users WHERE name = ?", ("Alice",))
        assert result["name"] == "Alice"

    def test_query_one_returns_none_when_no_match(self, repository):
        """Test query_one method returns None when no match found."""
        repository.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")

        result = repository.query_one("SELECT * FROM users WHERE id = ?", (999,))
        assert result is None

    def test_query_one_returns_first_match(self, repository):
        """Test query_one method returns first matching row."""
        repository.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")
        repository.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))
        repository.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))

        result = repository.query_one("SELECT * FROM users WHERE name = ?", ("Alice",))
        assert result["name"] == "Alice"

    def test_query_returns_row_objects(self, repository):
        """Test that query returns sqlite3.Row objects for column access."""
        repository.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)")
        repository.execute("INSERT INTO users (name, email) VALUES (?, ?)", ("Alice", "alice@example.com"))

        result = repository.query("SELECT * FROM users")
        row = result[0]

        # Test dict-style access
        assert row["name"] == "Alice"
        assert row["email"] == "alice@example.com"

        # Test index-style access
        assert row[1] == "Alice"
        assert row[2] == "alice@example.com"

    def test_close_closes_connection(self, temp_db):
        """Test close method closes the database connection."""
        repo = Repository(temp_db)
        assert repo.conn is not None

        repo.close()
        # After close, conn should be None or closed
        assert repo.conn is None

    def test_multiple_operations_in_transaction(self, repository):
        """Test that multiple operations are properly transactional."""
        repository.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)")

        # Multiple operations should work correctly
        repository.execute("INSERT INTO users (name) VALUES (?)", ("User1",))
        repository.execute("INSERT INTO users (name) VALUES (?)", ("User2",))
        repository.execute("INSERT INTO users (name) VALUES (?)", ("User3",))

        result = repository.query("SELECT COUNT(*) as count FROM users")
        assert result[0]["count"] == 3

    def test_execute_with_null_params(self, repository):
        """Test execute method with NULL parameters."""
        repository.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
        repository.execute("INSERT INTO users (name, age) VALUES (?, ?)", ("Alice", None))

        result = repository.query("SELECT * FROM users WHERE age IS NULL")
        assert len(result) == 1
        assert result[0]["name"] == "Alice"
