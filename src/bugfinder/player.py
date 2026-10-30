from __future__ import annotations

from .map import GameMap


class Player:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    def try_move(self, dx: int, dy: int, game_map: GameMap) -> bool:
        nx, ny = self.x + dx, self.y + dy
        if game_map.is_walkable(nx, ny):
            self.x, self.y = nx, ny
            return True
        return False
