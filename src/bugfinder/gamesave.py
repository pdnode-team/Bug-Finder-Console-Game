import json
from typing import Any


class GameSave:
    def __init__(self, filename: str) -> None:
        self.filename = filename

    def save(self, data: Any):
        with open(self.filename, "w", encoding="UTF-8") as f:
            json.dump(data, f, indent=2)

    def load(self) -> Any:
        with open(self.filename, "r", encoding="utf-8") as f:
            return json.load(f)
