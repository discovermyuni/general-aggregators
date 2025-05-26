import importlib.util
import os

SETTINGS_FILE = os.environ.get("AGGREGATOR_SETTINGS_MODULE", "config/settings.py")

class SettingsStore:
    _instance = None
    _settings = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load_settings(self):
        if self._settings is not None:
            return self._settings

        spec = importlib.util.spec_from_file_location("settings", SETTINGS_FILE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        self._settings = {var: getattr(module, var) for var in dir(module) if var.isupper()}
        return self._settings

def _load_settings():
    return SettingsStore().load_settings()


def get_setting(name: str):
    """Get a setting by name or raise KeyError if it does not exist."""
    settings = _load_settings()
    if name not in settings:
        msg = f"Setting '{name}' not found."
        raise KeyError(msg)
    return settings[name]


def get_setting_or_default(name: str, default_value):
    """Get a setting by name or return a default value if it does not exist."""
    return _load_settings().get(name, default_value)


def get_setting_or_none(name: str):
    """Get a setting by name or return None if it does not exist."""
    return _load_settings().get(name, None)
