from __future__ import annotations

from .map import GameMap


class Enemy:
    def __init__(
        self, symbol: str, x: int, y: int, damage: int = 1, dx: int = 1, dy: int = 0
    ) -> None:
        self.symbol = symbol
        self.x = x
        self.y = y
        self.damage = damage
        self.move_timer = 0.0
        self.dx = dx
        self.dy = dy

    def is_adjacent(self, px: int, py: int) -> bool:
        return abs(self.x - px) + abs(self.y - py) == 1

    def try_move(self, game_map: GameMap) -> None:  # ENEMY!!!
        new_x = self.x + self.dx
        new_y = self.y + self.dy

        if game_map.is_walkable(new_x, new_y):
            self.x = new_x
            self.y = new_y
        else:
            self.dx = -self.dx
            self.dy = -self.dy


class SlowEnemy(Enemy):
    def __init__(
        self, symbol: str, x: int, y: int, damage: int = 0, dx: int = 2, dy: int = 0
    ) -> None:
        super().__init__(symbol, x, y, damage)
        self.dx = dx
        self.dy = dy

    def try_move(self, game_map: GameMap) -> None:
        step_x = 1 if self.dx > 0 else (-1 if self.dx < 0 else 0)
        step_y = 1 if self.dy > 0 else (-1 if self.dy < 0 else 0)
        steps = max(abs(self.dx), abs(self.dy))

        moved = False
        for _ in range(steps):
            next_x = self.x + step_x
            next_y = self.y + step_y
            if game_map.is_walkable(next_x, next_y):
                self.x = next_x
                self.y = next_y
                moved = True
            else:
                break

        if not moved:
            self.dx = -self.dx
            self.dy = -self.dy
