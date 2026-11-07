"""Portable, versioned .mflow scenarios with strict import validation.

Imported automation is never run automatically. It can control the desktop,
so users must review imported steps and explicitly start execution.
"""
import copy
import json
from pathlib import Path
from uuid import uuid4

from .store import fresh_script, with_defaults

FORMAT = "macroflow.scenarios"
SCHEMA_VERSION = 1
MAX_FILE_SIZE = 2 * 1024 * 1024
MAX_SCRIPTS = 300
MAX_STEPS = 5000
SUPPORTED_ACTIONS = {"click", "double_click", "type_text", "press_key", "wait", "find_text"}


def dumps(scripts):
    if len(scripts) > MAX_SCRIPTS:
        raise ValueError("Слишком много сценариев для одного файла")
    return json.dumps({"format": FORMAT, "schema_version": SCHEMA_VERSION,
                       "scenarios": scripts}, ensure_ascii=False, indent=2)


def write_file(path, scripts):
    p = Path(path)
    content = dumps(scripts)
    if len(content.encode("utf-8")) > MAX_FILE_SIZE:
        raise ValueError("Экспорт превышает допустимый размер 2 МБ")
    p.write_text(content, encoding="utf-8")


def parse_file(path):
    p = Path(path)
    if p.stat().st_size > MAX_FILE_SIZE:
        raise ValueError("Файл слишком большой (максимум 2 МБ)")
    document = json.loads(p.read_text(encoding="utf-8-sig"))
    if isinstance(document, dict) and document.get("format") == FORMAT:
        if document.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("Неподдерживаемая версия формата сценария")
        entries = document.get("scenarios")
    elif isinstance(document, list):
        # Legacy plain-JSON scenario export.
        entries = document
    elif isinstance(document, dict) and "steps" in document:
        entries = [document]
    else:
        raise ValueError("Файл не похож на сценарии MacroFlow")

    if not isinstance(entries, list) or not 1 <= len(entries) <= MAX_SCRIPTS:
        raise ValueError("Файл должен содержать от 1 до 300 сценариев")

    result = []
    for number, raw in enumerate(entries, 1):
        if not isinstance(raw, dict) or not isinstance(raw.get("steps"), list):
            raise ValueError(f"Сценарий №{number}: неверная структура")
        if len(raw["steps"]) > MAX_STEPS:
            raise ValueError(f"Сценарий №{number}: слишком много действий")
        scenario = with_defaults(raw)
        if not isinstance(scenario.get("name"), str) or not scenario["name"].strip():
            raise ValueError(f"Сценарий №{number}: отсутствует название")
        if len(scenario["name"]) > 120:
            raise ValueError(f"Сценарий №{number}: слишком длинное название")
        if not isinstance(scenario.get("description", ""), str):
            raise ValueError(f"Сценарий №{number}: неверное описание")
        if not isinstance(scenario.get("global_delay_ms"), int) or not 0 <= scenario["global_delay_ms"] <= 120000:
            raise ValueError(f"Сценарий №{number}: неверная задержка")
        for index, step in enumerate(scenario["steps"], 1):
            if not isinstance(step, dict) or step.get("action") not in SUPPORTED_ACTIONS:
                raise ValueError(f"Сценарий №{number}, шаг {index}: неизвестное действие")
            if not isinstance(step.get("text", ""), str) or len(step.get("text", "")) > 10000:
                raise ValueError(f"Сценарий №{number}, шаг {index}: неверный текст")
            if not isinstance(step.get("delay_ms", 0), int) or not 0 <= step.get("delay_ms", 0) <= 120000:
                raise ValueError(f"Сценарий №{number}, шаг {index}: неверная задержка")
            region = step.get("region")
            if region is not None:
                if not isinstance(region, dict) or not all(isinstance(region.get(k), int) for k in ("x", "y", "w", "h")) or region["w"] <= 0 or region["h"] <= 0:
                    raise ValueError(f"Сценарий №{number}, шаг {index}: неверная область")
        # Allocate fresh IDs to prevent collisions and never overwrite existing scripts.
        scenario = copy.deepcopy(scenario)
        scenario["id"] = str(uuid4())
        for step in scenario["steps"]:
            step["id"] = str(uuid4())
        result.append(scenario)
    return result
