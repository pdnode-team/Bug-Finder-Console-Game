from __future__ import annotations

import re
from typing import Any

TAG_RE = re.compile(r"\[/?[^\]]+\]")


class GameMap:
    def __init__(self, lines: list[Any]) -> None:
        self.tiles: list[list[str]] = [list(row) for row in lines]
        self.height: int = len(self.tiles)
        self.width: int = len(self.tiles[0]) if self.tiles else 0

    def is_walkable(self, x: int, y: int) -> bool:
        if not (0 <= y < self.height and 0 <= x < self.width):
            return False
        clean_char = TAG_RE.sub("", self.tiles[y][x])
        return clean_char == "."

    def set_tile(self, x: int, y: int, ch: str) -> None:
        if 0 <= y < self.height and 0 <= x < self.width:
            self.tiles[y][x] = ch

    def render(self, player_x: int, player_y: int, entities: list[Any]) -> str:
        lines: list[str] = []
        for y, row in enumerate(self.tiles):
            line_chars: list[str] = []
            for x, ch in enumerate(row):
                if x == player_x and y == player_y:
                    line_chars.append("[bold cyan]@[/] ")
                else:
                    entity = next((e for e in entities if e.x == x and e.y == y), None)
                    if entity:
                        symbol = getattr(entity, "symbol", "?")
                        line_chars.append(f"{symbol} ")
                    else:
                        clean = TAG_RE.sub("", ch)
                        line_chars.append(clean[:1] + " ")
            lines.append("".join(line_chars))
        return "\n".join(lines)
