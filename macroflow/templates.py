"""Optional starter templates. Placeholder actions are disabled until configured."""
from .store import fresh_script, fresh_step

TEMPLATES = {
    "Документы 1С": (
        "Заготовка для открытия, изменения и проведения документа.",
        [("double_click", "Открыть документ"),
         ("click", "Открыть выбор контрагента"),
         ("type_text", "Ввести данные контрагента"),
         ("press_key", "Подтвердить выбор"),
         ("click", "Провести и закрыть")],
    ),
    "Заполнение формы": (
        "Для ввода повторяющихся данных в поля Windows-приложения.",
        [("click", "Выбрать поле"), ("type_text", "Ввести значение"),
         ("press_key", "Перейти к следующему полю")],
    ),
    "Повторяющиеся клики": (
        "Шаблон однотипных действий с задержкой в миллисекундах.",
        [("click", "Нажать первую кнопку"), ("wait", "Подождать"),
         ("click", "Нажать вторую кнопку")],
    ),
}


def build_template(name):
    description, actions = TEMPLATES[name]
    scenario = fresh_script(name)
    scenario["description"] = description
    for action, title in actions:
        step = fresh_step(action)
        step["enabled"] = False  # avoid clicking before the user configures targets
        if action == "press_key":
            step["text"] = "tab" if name == "Заполнение формы" else "enter"
        scenario["steps"].append(step)
    return scenario
