from unittest import mock

from mopidy_scrobbler import Extension
from mopidy_scrobbler import frontend as frontend_lib


def test_get_default_config():
    # Create an instance of the Extension class
    ext = Extension()

    # Obtain the default configuration
    config = ext.get_default_config()

    # Check if certain expected strings are present in the default config
    assert "[scrobbler]" in config
    assert "enabled = true" in config
    assert "username =" in config
    assert "password =" in config


def test_get_config_schema():
    # Create an instance of the Extension class
    ext = Extension()

    # Obtain the configuration schema
    schema = ext.get_config_schema()

    # Check if 'username' and 'password' are keys in the schema
    assert "username" in schema
    assert "password" in schema


def test_setup():
    # Create an instance of the Extension class
    ext = Extension()

    # Create a mock object representing the registry
    registry = mock.Mock()

    # Call the setup method with the mock registry
    ext.setup(registry)

    # Assert that the 'add' method of the registry was called with expected arguments
    registry.add.assert_called_once_with("frontend", frontend_lib.ScrobblerFrontend)
