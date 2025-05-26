import os
import importlib.util

SETTINGS_FILE = os.environ.get("AGGREGATOR_SETTINGS_MODULE", "config/settings.py")

_settings = None

def _load_settings():
    global _settings
    if _settings is not None:
        return _settings

    spec = importlib.util.spec_from_file_location("settings", SETTINGS_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    _settings = {var: getattr(module, var) for var in dir(module) if var.isupper()}
    return _settings


def get_setting(name: str):
    """Get a setting by name or raise KeyError if it does not exist."""
    settings = _load_settings()
    if name not in settings:
        raise KeyError(f"Setting '{name}' not found.")
    return settings[name]


def get_setting_or_default(name: str, default_value):
    """Get a setting by name or return a default value if it does not exist."""
    return _load_settings().get(name, default_value)    


def get_setting_or_none(name: str):
    """Get a setting by name or return None if it does not exist."""
    return _load_settings().get(name, None)
