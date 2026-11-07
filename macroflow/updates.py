"""Check public GitHub Releases without a token. No silent executable installation."""
import json
import re
from urllib.request import Request, urlopen
from PySide6.QtCore import QThread, Signal
from . import __version__, GITHUB_REPOSITORY


def version_tuple(s):
    numbers = re.match(r"^v?(\d+)\.(\d+)\.(\d+)", s)
    return tuple(int(v) for v in numbers.groups()) if numbers else (0, 0, 0)


class UpdateCheck(QThread):
    result = Signal(str, str, bool)
    error = Signal(str)

    def run(self):
        try:
            request = Request(
                f"https://api.github.com/repos/{GITHUB_REPOSITORY}/releases/latest",
                headers={"Accept": "application/vnd.github+json", "User-Agent": f"MacroFlow/{__version__}"},
            )
            with urlopen(request, timeout=12) as response:
                info = json.load(response)
            latest = info["tag_name"]
            url = info["html_url"]
            self.result.emit(latest, url, version_tuple(latest) > version_tuple(__version__))
        except Exception as exc:
            self.error.emit(str(exc))
