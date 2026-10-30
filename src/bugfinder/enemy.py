from __future__ import annotations

from .map import GameMap


class Enemy:
    def __init__(self, symbol: str, x: int, y: int, damage: int = 1) -> None:
        self.symbol = symbol
        self.x = x
        self.y = y
        self.damage = damage
        self.move_timer = 0.0
        self.dx = 1
        self.dy = 0

    def is_adjacent(self, px: int, py: int) -> bool:
        return abs(self.x - px) + abs(self.y - py) == 1

    def try_move(self, game_map: GameMap) -> None:  # ENEMY!!!
        new_x = self.x + self.dx
        new_y = self.y + self.dy

        if game_map.is_walkable(new_x, new_y):
            self.x = new_x
            self.y = new_y
        else:
            # 碰到墙，方向取反
            self.dx = -self.dx
            self.dy = -self.dy
