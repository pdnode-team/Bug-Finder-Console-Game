from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Choice:
    label: str
    reply: str

class Npc:
    def __init__(
        self,
        symbol: str,
        x: int,
        y: int,
        dialog: list[str],
        choices: list[Choice] | None = None,
    ) -> None:
        self.symbol = symbol
        self.x = x
        self.y = y
        self.dialog = dialog
        self.choices = choices or []
        self.dialog_index = 0
        self.talked = False
        

    def current_line(self) -> str:
        if 0 <= self.dialog_index < len(self.dialog):
            return self.dialog[self.dialog_index]
        return ""

    def advance(self) -> bool:
        if self.dialog_index + 1 < len(self.dialog):
            self.dialog_index += 1
            return True
        return False

    def reset(self) -> None:
        self.dialog_index = 0

    def is_adjacent(self, px: int, py: int) -> bool:
        return abs(self.x - px) <= 1 and abs(self.y - py) <= 1 and not (self.x == px and self.y == py)