"""Store scripts in user data, never in the installed program directory."""
import json
import os
from pathlib import Path
from uuid import uuid4


def data_directory() -> Path:
    base = Path(os.environ.get("APPDATA") or Path.home() / ".config")
    result = base / "MacroFlow"
    result.mkdir(parents=True, exist_ok=True)
    return result


FILE = "scenarios.json"


def fresh_script(name="Новый сценарий"):
    return {"id": str(uuid4()), "name": name, "global_delay_ms": 0, "steps": []}


def fresh_step(action="click"):
    return {"id": str(uuid4()), "action": action, "delay_ms": 300,
            "enabled": True, "region": None, "text": ""}


def load_scripts():
    path = data_directory() / FILE
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
    except (OSError, ValueError):
        # Malformed input is never overwritten automatically.
        raise RuntimeError(f"Не удалось прочитать сценарии: {path}")
    raise RuntimeError("Неверный формат файла сценариев")


def save_scripts(scripts):
    path = data_directory() / FILE
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(scripts, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)
