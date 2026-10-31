from __future__ import annotations

from typing import ClassVar

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Static

from bugfinder.enemy import Enemy
from bugfinder.gamesave import GameSave
from bugfinder.start_ui import StartScene

from .map import GameMap
from .npc import Choice, Npc
from .player import Player

npcs: dict[str, list[Npc]] = {
    "init_room": [
        Npc(
            "H",
            12,
            5,
            [
                "Hello!",
                "Welcome to ██████",
                "This place is very old and fragile",
                "If you want to escape...",
                "You can look for bugs and reduce system stability",
            ],
            choices=[
                Choice("Who is ███?", "I cannot tell you..."),
                Choice("Why am I here?", "I have no idea..."),
            ],
        )
    ],
    "room2": [
        Npc(
            "H",
            4,
            2,
            [
                "Hello!",
                "This is your first challenge.",
                'You need to go to the console [yellow]"C"[/] to exploit to reduce system stability',
                'Please watch out for the [red]"E"[/] along the way. It the safety system.',
                "Lets Go!",
            ],
        )
    ],
}

enemies: dict[str, list[Enemy]] = {
    "room2": [
        Enemy("E", 10, 5),
        Enemy("E", 15, 8),
    ],
}


class TalkPhase:
    LINES = "lines"
    CHOOSING = "choosing"
    REPLY = "reply"


class BugFinder(App[None]):
    CSS = """
    #map { height: 1fr; border: solid gray; }
    #dialog { height: 8; border: solid gray; }
    """

    BINDINGS: ClassVar = [
        Binding("q", "quit", "Quit"),
        Binding("w", "move_up"),
        Binding("s", "move_down"),
        Binding("a", "move_left"),
        Binding("d", "move_right"),
        Binding("e", "talk"),
        Binding("space", "continue_dialog"),
        Binding("1", "choose_1"),
        Binding("2", "choose_2"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.move_cooldown = False
        self.move_delay = 0.06
        self.maps = {
            "init_room": [
                "####################",
                "#..................#",
                "#..................#",
                "#..................#",
                "#..................#",
                "#...........H......#",
                "#..................#",
                "#..................#",
                "#..................#",
                "####################",
            ],
            "room2": [
                "#####################################",
                "#.......#...........................#",
                "#.......#...........................#",
                "#.......#...........................#",
                "#.......#...........................#",
                "#.......#...........................#",
                "#.......#...........................#",
                "#.......###################.........#",
                "#.......#...........................#",
                "#.......#...........................#",
                "#.......#...........................#",
                "#.......#...........................#",
                "#.......#...........................#",
                "#.......#...........................#",
                "#.......#...........................#",
                "#.......#...........................#",
                "#.......#...........................#",
                "#.......#...........................#",
                "#.......#...........................#",
                "#...................................#",
                "#...................................#",
                "#...................................#",
                "#...................................#",
                "#...................................#",
                "#...................................#",
                "#####################################",
            ],
        }
        self.current_map_name = "init_room"
        self.game_map = GameMap(self.maps[self.current_map_name])

        self.player = Player(2, 2)
        self.npcs = npcs["init_room"]
        self.talking_to: int | None = None
        self.talk_phase = TalkPhase.LINES
        self.reply_index = 0

        self.enemies: list[Enemy] = []

        self.enemy_alert: str | None = None

        self.saver = GameSave("data.json")
        self.gamesave = self.saver.load()

        if self.gamesave:
            room = self.gamesave.get("room", "init_room")
            px = self.gamesave.get("player_x", 2)
            py = self.gamesave.get("player_y", 2)

            if room in self.maps:
                self.current_map_name = room
                self.game_map = GameMap(self.maps[room])
                self.player = Player(px, py)

                if room == "room2":
                    self.npcs = npcs["room2"]
                    self.enemies = enemies["room2"]

    def _can_move(self) -> bool:
        return self.talking_to is None and not self.move_cooldown

    def _start_cooldown(self) -> None:
        self.move_cooldown = True
        self.set_timer(self.move_delay, self._end_cooldown)

    def _end_cooldown(self) -> None:
        self.move_cooldown = False

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(id="map")
            yield Static(id="dialog")

    def on_mount(self) -> None:
        self.update_display()

        self.set_interval(0.6, self._tick_enemies)

    def update_display(self) -> None:
        entities = self.npcs + self.enemies
        map_text = self.game_map.render(self.player.x, self.player.y, entities)
        self.query_one("#map", Static).update(map_text)

        dialog = self.query_one("#dialog", Static)

        if self.enemy_alert:
            dialog.update(self.enemy_alert)
            return

        if self.talking_to is not None:
            npc = self.npcs[self.talking_to]
            if self.talk_phase == TalkPhase.LINES:
                dialog.update(f"{npc.current_line()}\n\n[dim]Space to continue[/]")
            elif self.talk_phase == TalkPhase.CHOOSING:
                text = "Choose:\n" + "\n".join(
                    f"{i + 1}. {c.label}" for i, c in enumerate(npc.choices)
                )
                dialog.update(text)
            elif self.talk_phase == TalkPhase.REPLY:
                reply = npc.choices[self.reply_index].reply if npc.choices else ""
                dialog.update(f"{reply}\n\n[dim]Space to close[/]")
        else:
            near = any(n.is_adjacent(self.player.x, self.player.y) for n in self.npcs)
            if self.npcs and self.npcs[0].talked:
                dialog.update("[dim]Go to the exit[/]")
            elif near:
                dialog.update("[dim]Press E to talk[/]")
            else:
                dialog.update("[dim]Approach the NPC[/]")

        # talked
        if self.npcs and self.npcs[0].talked and self.current_map_name == "init_room":
            self.game_map.set_tile(19, 5, "[green on green].[/]")

        if (
            self.player.x == 19
            and self.player.y == 5
            and self.current_map_name == "init_room"
        ):
            self.switch_to("room2", 1, 2)

    def action_move_up(self) -> None:
        if not self._can_move():
            return
        new_x = self.player.x
        new_y = self.player.y - 1
        if self.game_map.is_walkable(new_x, new_y) and not self._is_blocked_by_entity(
            new_x, new_y
        ):
            self.player.try_move(0, -1, self.game_map)
            self.update_display()
            self._start_cooldown()
            self._check_enemy_collision()

    def action_move_down(self) -> None:
        if not self._can_move():
            return
        new_x = self.player.x
        new_y = self.player.y + 1
        if self.game_map.is_walkable(new_x, new_y) and not self._is_blocked_by_entity(
            new_x, new_y
        ):
            self.player.try_move(0, 1, self.game_map)
            self.update_display()
            self._start_cooldown()
            self._check_enemy_collision()

    def action_move_left(self) -> None:
        if not self._can_move():
            return
        new_x = self.player.x - 1
        new_y = self.player.y
        if self.game_map.is_walkable(new_x, new_y) and not self._is_blocked_by_entity(
            new_x, new_y
        ):
            self.player.try_move(-1, 0, self.game_map)
            self.update_display()
            self._start_cooldown()
            self._check_enemy_collision()

    def action_move_right(self) -> None:
        if not self._can_move():
            return
        new_x = self.player.x + 1
        new_y = self.player.y
        if self.game_map.is_walkable(new_x, new_y) and not self._is_blocked_by_entity(
            new_x, new_y
        ):
            self.player.try_move(1, 0, self.game_map)
            self.update_display()
            self._start_cooldown()
            self._check_enemy_collision()

    def action_talk(self) -> None:
        if self.talking_to is not None:
            return
        for i, npc in enumerate(self.npcs):
            if npc.is_adjacent(self.player.x, self.player.y):
                self.talking_to = i
                npc.reset()
                self.talk_phase = TalkPhase.LINES
                self.update_display()
                return

    def action_continue_dialog(self) -> None:
        if self.talking_to is None:
            return
        npc = self.npcs[self.talking_to]

        if self.talk_phase == TalkPhase.LINES:
            if not npc.advance():
                if npc.choices:
                    self.talk_phase = TalkPhase.CHOOSING
                else:
                    npc.talked = True
                    self.talking_to = None
        elif self.talk_phase == TalkPhase.REPLY:
            npc.talked = True
            self.talking_to = None
            self.talk_phase = TalkPhase.LINES

        self.update_display()

    def action_choose_1(self) -> None:
        self._choose(0)

    def action_choose_2(self) -> None:
        self._choose(1)

    def _choose(self, index: int) -> None:
        if self.talking_to is None or self.talk_phase != TalkPhase.CHOOSING:
            return
        npc = self.npcs[self.talking_to]
        if index < len(npc.choices):
            self.reply_index = index
            self.talk_phase = TalkPhase.REPLY
            self.update_display()

    async def action_quit(self) -> None:
        self.exit()

    def switch_to(self, map_name: str, player_x: int = 2, player_y: int = 2) -> None:
        if map_name in self.maps:
            self.current_map_name = map_name
            self.game_map = GameMap(self.maps[map_name])
            self.player.x = player_x
            self.player.y = player_y
            self.talking_to = None

            self.saver.save(
                {
                    "room": map_name,
                    "player_x": player_x,
                    "player_y": player_y,
                }
            )

            self.npcs = npcs[map_name]
            self.enemies = enemies[map_name]
        else:
            self.enemies = []

            self.update_display()

    def _tick_enemies(self) -> None:
        if self.talking_to is not None or self.enemy_alert:
            return
        self._check_enemy_collision()
        for enemy in self.enemies:
            enemy.try_move(self.game_map)
        self.update_display()

    def _check_enemy_collision(self) -> None:
        if self.enemy_alert:
            return
        for enemy in self.enemies:
            if enemy.is_adjacent(self.player.x, self.player.y) or (
                enemy.x == self.player.x and enemy.y == self.player.y
            ):
                self._on_enemy_touch(enemy)
                break

    def _on_enemy_touch(self, enemy: Enemy) -> None:
        self.enemy_alert = "Firewall: [bold red]Unauthorized Action![/]"
        self.set_timer(1.5, self._clear_enemy_alert)

    def _clear_enemy_alert(self) -> None:
        self.enemy_alert = None
        self.update_display()

    def _is_blocked_by_entity(self, x: int, y: int) -> bool:
        for npc in self.npcs:
            if npc.x == x and npc.y == y:
                return True
        for enemy in self.enemies:
            if enemy.x == x and enemy.y == y:
                return True
        return False


def main() -> None:
    result = StartScene().run()
    if result == "start":
        BugFinder().run()


if __name__ == "__main__":
    main()
