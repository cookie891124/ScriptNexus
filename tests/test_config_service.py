"""Tests for ConfigService class."""

import os
import shutil
import tempfile
import json
import pytest

from core.config_service import ConfigService


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    fd, path = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    yield path
    os.unlink(path)


@pytest.fixture
def config_service(temp_config_file):
    """Create a ConfigService instance for testing."""
    return ConfigService(temp_config_file)


class TestConfigServiceInit:
    """Test ConfigService initialization."""

    def test_init_with_valid_path(self, temp_config_file):
        """Test initialization with valid config path."""
        service = ConfigService(temp_config_file)
        assert service.config_path == temp_config_file

    def test_init_creates_directory(self):
        """Test that save creates directory if it doesn't exist."""
        temp_dir = tempfile.mkdtemp()
        config_path = os.path.join(temp_dir, 'subdir', 'config.json')

        try:
            service = ConfigService(config_path)
            service.save({"key": "value"})
            assert os.path.exists(config_path)
        finally:
            shutil.rmtree(temp_dir)


class TestLoad:
    """Test load method."""

    def test_load_empty_file(self, temp_config_file):
        """Test loading an empty config file."""
        with open(temp_config_file, 'w', encoding='utf-8') as f:
            f.write('{}')

        service = ConfigService(temp_config_file)
        result = service.load()
        assert result == {}

    def test_load_with_data(self, temp_config_file):
        """Test loading config with data."""
        data = {"key1": "value1", "key2": 123}
        with open(temp_config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)

        service = ConfigService(temp_config_file)
        result = service.load()
        assert result == data

    def test_load_nonexistent_file(self, temp_config_file):
        """Test loading when file doesn't exist."""
        # Don't create the file
        service = ConfigService(temp_config_file)
        result = service.load()
        assert result == {}

    def test_load_invalid_json(self, temp_config_file):
        """Test loading invalid JSON returns empty dict."""
        with open(temp_config_file, 'w', encoding='utf-8') as f:
            f.write('invalid json')

        service = ConfigService(temp_config_file)
        result = service.load()
        assert result == {}


class TestSave:
    """Test save method."""

    def test_save_new_file(self, temp_config_file):
        """Test saving config to new file."""
        data = {"key": "value"}
        service = ConfigService(temp_config_file)
        service.save(data)

        assert os.path.exists(temp_config_file)
        with open(temp_config_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        assert saved_data == data

    def test_save_overwrites_existing(self, temp_config_file):
        """Test saving overwrites existing config."""
        # Create initial config
        with open(temp_config_file, 'w', encoding='utf-8') as f:
            json.dump({"old": "data"}, f)

        service = ConfigService(temp_config_file)
        service.save({"new": "data"})

        with open(temp_config_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        assert saved_data == {"new": "data"}

    def test_save_creates_directory(self):
        """Test that save creates directory if it doesn't exist."""
        temp_dir = tempfile.mkdtemp()
        config_path = os.path.join(temp_dir, 'subdir', 'config.json')

        try:
            service = ConfigService(config_path)
            service.save({"key": "value"})
            assert os.path.exists(config_path)
        finally:
            shutil.rmtree(temp_dir)

    def test_save_uses_utf8_encoding(self, temp_config_file):
        """Test that save uses UTF-8 encoding."""
        data = {"unicode": "测试中文"}
        service = ConfigService(temp_config_file)
        service.save(data)

        with open(temp_config_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        assert saved_data == data


class TestGet:
    """Test get method."""

    def test_get_existing_key(self, config_service):
        """Test getting an existing key."""
        config_service.save({"key1": "value1"})
        result = config_service.get("key1")
        assert result == "value1"

    def test_get_nonexistent_key(self, config_service):
        """Test getting a nonexistent key returns None."""
        config_service.save({"key1": "value1"})
        result = config_service.get("nonexistent")
        assert result is None

    def test_get_with_default(self, config_service):
        """Test getting a nonexistent key returns default value."""
        config_service.save({"key1": "value1"})
        result = config_service.get("nonexistent", "default_value")
        assert result == "default_value"

    def test_get_nested_value(self, config_service):
        """Test getting a nested value using dot notation."""
        config_service.save({
            "database": {
                "host": "localhost",
                "port": 5432
            }
        })
        result = config_service.get("database.host")
        assert result == "localhost"

        result = config_service.get("database.port")
        assert result == 5432

    def test_get_nested_nonexistent(self, config_service):
        """Test getting nonexistent nested key."""
        config_service.save({"key1": "value1"})
        result = config_service.get("database.host", "default")
        assert result == "default"


class TestSet:
    """Test set method."""

    def test_set_new_key(self, config_service):
        """Test setting a new key."""
        config_service.set("key1", "value1")
        assert config_service.get("key1") == "value1"

    def test_set_overwrites_existing(self, config_service):
        """Test setting overwrites existing key."""
        config_service.set("key1", "value1")
        config_service.set("key1", "value2")
        assert config_service.get("key1") == "value2"

    def test_set_nested_key(self, config_service):
        """Test setting a nested key using dot notation."""
        config_service.set("database.host", "localhost")
        config_service.set("database.port", 5432)

        assert config_service.get("database.host") == "localhost"
        assert config_service.get("database.port") == 5432

    def test_set_persists_to_file(self, temp_config_file):
        """Test that set persists changes to file after save."""
        service = ConfigService(temp_config_file)
        service.set("key1", "value1")
        service.save()

        with open(temp_config_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        assert saved_data == {"key1": "value1"}

    def test_set_with_various_types(self, config_service):
        """Test setting values with various types."""
        config_service.set("string_val", "hello")
        config_service.set("int_val", 42)
        config_service.set("float_val", 3.14)
        config_service.set("bool_val", True)
        config_service.set("list_val", [1, 2, 3])
        config_service.set("dict_val", {"nested": "value"})

        assert config_service.get("string_val") == "hello"
        assert config_service.get("int_val") == 42
        assert config_service.get("float_val") == 3.14
        assert config_service.get("bool_val") is True
        assert config_service.get("list_val") == [1, 2, 3]
        assert config_service.get("dict_val") == {"nested": "value"}


class TestDelete:
    """Test delete method."""

    def test_delete_existing_key(self, config_service):
        """Test deleting an existing key."""
        config_service.set("key1", "value1")
        config_service.set("key2", "value2")

        config_service.delete("key1")

        assert config_service.get("key1") is None
        assert config_service.get("key2") == "value2"

    def test_delete_nonexistent_key(self, config_service):
        """Test deleting a nonexistent key doesn't raise error."""
        # Should not raise an error
        config_service.delete("nonexistent")

    def test_delete_nested_key(self, config_service):
        """Test deleting a nested key using dot notation."""
        config_service.set("database.host", "localhost")
        config_service.set("database.port", 5432)

        config_service.delete("database.host")

        assert config_service.get("database.host") is None
        assert config_service.get("database.port") == 5432

    def test_delete_persists_to_file(self, temp_config_file):
        """Test that delete persists changes to file after save."""
        service = ConfigService(temp_config_file)
        service.set("key1", "value1")
        service.set("key2", "value2")
        service.save()

        service.delete("key1")
        service.save()

        with open(temp_config_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
        assert "key1" not in saved_data
        assert saved_data["key2"] == "value2"


class TestLoadAndSaveIntegration:
    """Integration tests for load and save."""

    def test_save_then_load(self, temp_config_file):
        """Test saving then loading returns same data."""
        data = {
            "string": "value",
            "number": 42,
            "nested": {"key": "value"}
        }

        service = ConfigService(temp_config_file)
        service.save(data)
        result = service.load()

        assert result == data

    def test_set_save_reload(self, temp_config_file):
        """Test set, save, then reload in new instance."""
        service1 = ConfigService(temp_config_file)
        service1.set("key1", "value1")
        service1.set("key2", "value2")
        service1.save()

        service2 = ConfigService(temp_config_file)
        result = service2.load()

        assert result == {"key1": "value1", "key2": "value2"}

    def test_full_workflow(self, temp_config_file):
        """Test a full workflow of set, get, save, load, delete."""
        service = ConfigService(temp_config_file)

        # Set values
        service.set("app.name", "MyApp")
        service.set("app.version", "1.0.0")
        service.set("debug", True)

        # Save to file
        service.save()

        # Load in new instance
        service2 = ConfigService(temp_config_file)
        config = service2.load()

        # Use get method for dot notation access
        assert service2.get("app.name") == "MyApp"
        assert service2.get("app.version") == "1.0.0"
        assert service2.get("debug") is True

        # Delete and save
        service2.delete("debug")
        service2.save()

        # Verify deletion
        service3 = ConfigService(temp_config_file)
        config = service3.load()
        assert service3.get("debug") is None
