from aqt import mw
from typing import Dict, Any, cast
from aqt.utils import showWarning

def load_config() -> Dict[str, Any]:
    try:
        config = mw.addonManager.getConfig(__name__)
        if config is None:
            showWarning("No config found. Please set up the add-on config via Anki's Add-on Manager.")
            return {}
        return cast(Dict[str, Any], config)
    except Exception as e:
        showWarning(f"Error loading config: {e}")
        return {}

def save_config(config: Dict[str, Any]) -> None:
    try:
        mw.addonManager.writeConfig(__name__, config)
    except Exception as e:
        showWarning(f"Error saving config: {e}") 