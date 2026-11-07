"""Durable user-owned scenarios. Installed files never contain user data."""
import json
import os
from pathlib import Path
from datetime import datetime
from uuid import uuid4

FILE = "scenarios.json"
REPEAT_MODES = ("once", "count", "forever")


def data_directory() -> Path:
    base = Path(os.environ.get("APPDATA") or Path.home() / ".config")
    result = base / "MacroFlow"
    result.mkdir(parents=True, exist_ok=True)
    return result


def fresh_script(name="Новый сценарий"):
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    return {
        "id": str(uuid4()), "name": name, "description": "",
        "global_delay_ms": 0, "repeat_mode": "once",
        "created_at": timestamp, "updated_at": timestamp,
        "repeat_count": 1, "cycle_delay_ms": 0, "steps": [],
    }


def fresh_step(action="click"):
    return {"id": str(uuid4()), "action": action, "delay_ms": 300,
            "enabled": True, "region": None, "text": ""}


def with_defaults(script):
    """Keep old (v0.1.0) saved documents compatible with new options."""
    if not isinstance(script, dict):
        raise ValueError("Неверный формат сценария")
    defaults = fresh_script()
    # A v0.1.0 scenario has no modification date: do not invent one.
    defaults["created_at"] = None
    defaults["updated_at"] = None
    value = {**defaults, **script}
    # Never generate a replacement ID for an existing legacy scenario.
    value["id"] = script.get("id") or str(uuid4())
    if value.get("repeat_mode") not in REPEAT_MODES:
        value["repeat_mode"] = "once"
    value["repeat_count"] = max(1, min(1000000, int(value.get("repeat_count") or 1)))
    value["cycle_delay_ms"] = max(0, min(120000, int(value.get("cycle_delay_ms") or 0)))
    if not isinstance(value.get("steps"), list):
        raise ValueError("Неверный список действий")
    return value


def load_scripts():
    path = data_directory() / FILE
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [with_defaults(s) for s in data]
    except (OSError, ValueError, TypeError) as exc:
        # Never overwrite invalid files automatically: they might be recoverable.
        raise RuntimeError(f"Не удалось прочитать сценарии: {path} ({exc})") from exc
    raise RuntimeError("Неверный формат файла сценариев")


def save_scripts(scripts):
    path = data_directory() / FILE
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(scripts, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)
