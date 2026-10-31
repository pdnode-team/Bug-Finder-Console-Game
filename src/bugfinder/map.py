from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .npc import Npc


import re

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

    def render(self, player_x: int, player_y: int, npcs: list[Any]) -> str:
        lines: list[str] = []
        for y, row in enumerate(self.tiles):
            line_chars: list[str] = []
            for x, ch in enumerate(row):
                if x == player_x and y == player_y:
                    line_chars.append("@ ")
                else:
                    npc_here: Npc | None = next(
                        (n for n in npcs if n.x == x and n.y == y), None
                    )
                    symbol = npc_here.symbol if npc_here else ch
                    clean = TAG_RE.sub("", symbol)
                    line_chars.append(clean[:1] + " ")
            lines.append("".join(line_chars))
        return "\n".join(lines)