from __future__ import annotations

import re
from typing import ClassVar

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Static

from bugfinder.enemy import ChaserEnemy, Enemy, SlowEnemy
from bugfinder.gamesave import GameSave
from bugfinder.map import GameMap
from bugfinder.npc import Choice, Npc
from bugfinder.player import Player
from bugfinder.start_ui import StartScene

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
    "level1": [
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
        ),
        Npc(
            "[yellow]C[/]",
            12,
            4,
            ["Console: .....Loading.....", "terra@bugfinder:~$ █"],
            choices=[
                Choice(
                    "sudo rm -rf /*",
                    "terra@bugfinder:~$ sudo rm -rf /*\nSystem: You better run right now otherwise you will stay with me forever haha!",  # So old-fashion
                )
            ],
        ),
    ],
    "level2": [
        Npc(
            "H",
            35,
            1,
            [
                "Nice!!!",
                "This time, you have a new enemy to focus on",
                '[yellow]"S"[/], it moves really fast, but it won\'t hit you, it will slow you down',
                "Keep going! (Go back! The start wall is unlocked!)",
            ],
            choices=[Choice("May I ask who you are?", "Let's not talk about that.")],
        ),
        Npc(
            "[green]C[/]",
            22,
            18,
            ["Console: .....Loading.....", "terra@bugfinder:~$ █"],
            choices=[
                Choice(
                    "sudo rm -rf /*",
                    "terra@bugfinder:~$ sudo rm -rf /*\n[red]System: I hope you are always that lucky[/]",  # So old-fashion
                )
            ],
        ),
    ],
    "level3": [
        Npc(
            "H",
            14,
            4,
            [
                "Unbelievable!",
                "This time, you also have a new enemy to focus on",
                '[yellow]"C"[/], it moves to you! please be careful!',
                "Go!",
            ],
            choices=[
                Choice(
                    "May I ask who you are?",
                    "I will tell you if you can pass this level, good luck.",
                )
            ],
        ),
        Npc(
            "[green]C[/]",
            17,
            1,
            ["Console: .....Loading.....", "terra@bugfinder:~$ █"],
            choices=[
                Choice(
                    "sudo rm -rf /*",
                    "terra@bugfinder:~$ sudo rm -rf /*\n[red]You won't have any chance to do same in next room[/]",
                )
            ],
        ),
    ],
}

enemies: dict[str, list[Enemy]] = {
    "level1": [
        Enemy("[bold red]E[/]", 35, 5),
        Enemy("[bold red]E[/]", 30, 8),
        Enemy("[bold red]E[/]", 10, 10),
        Enemy("[bold red]E[/]", 30, 13),
        Enemy("[bold red]E[/]", 10, 16),
        Enemy("[bold red]E[/]", 30, 20),
    ],
    "level2": [
        Enemy("[bold red]E[/]", 35, 5, dx=-1),
        Enemy("[bold red]E[/]", 30, 8),
        Enemy("[bold red]E[/]", 10, 10, dx=-1),
        Enemy("[bold red]E[/]", 30, 13),
        Enemy("[bold red]E[/]", 10, 16, dx=-1),
        Enemy("[bold red]E[/]", 30, 20),
        Enemy("[bold red]E[/]", 4, 3, dx=-1),
        Enemy("[bold red]E[/]", 4, 5),
        SlowEnemy("[bold yellow]S[/]", 3, 20, dy=2, dx=0),
        SlowEnemy("[bold yellow]S[/]", 3, 3, dy=0, dx=2),
        SlowEnemy("[bold yellow]S[/]", 3, 20, dy=0, dx=2),
        SlowEnemy("[bold yellow]S[/]", 30, 15, dy=2, dx=0),
        SlowEnemy("[bold yellow]S[/]", 35, 15, dy=2, dx=0),
    ],
    "level3": [
        Enemy("[bold red]E[/]", 3, 5, dy=1, dx=0),
        Enemy("[bold red]E[/]", 3, 15, dy=-1, dx=0),
        Enemy("[bold red]E[/]", 15, 3, dx=2),
        Enemy("[bold red]E[/]", 25, 4, dx=-2),
        SlowEnemy("[bold yellow]S[/]", 20, 7, dx=2, dy=0),
        SlowEnemy("[bold yellow]S[/]", 12, 11, dx=0, dy=2),
        Enemy("[bold red]E[/]", 32, 10, dy=0, dx=-1),
        Enemy("[bold red]E[/]", 30, 20, dy=-1, dx=0),
        ChaserEnemy("[bold magenta]C[/]", 18, 20),
        Enemy("[bold red]E[/]", 15, 28, dx=2),
        SlowEnemy("[bold yellow]S[/]", 25, 26, dx=-2, dy=0),
        Enemy("[bold red]B[/]", 17, 22),
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
        Binding("p", "pause", "Pause"),
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
            "level1": [
                "#####################################",
                "#.......#...........................#",
                "#.......#...........................#",
                "#.......#.................#.........#",
                "#.......#.................#.........#",
                "#.......#.................#.........#",
                "#.......#.................#.........#",
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
            "level2": [
                "#####################################",
                "#...................................#",
                "#--##################################",
                "#..#........................#.......#",
                "#.......#......##......#............#",
                "#..#...........##...........#.......#",
                "#############################.......#",
                "#...................................#",
                "#..........####.....................#",
                "#...................................#",
                "#....................################",
                "###############...........#.........#",
                "#.........................#.........#",
                "#......####################.........#",
                "#..............#....................#",
                "#...######.....#....................#",
                "#........#.....#.....############...#",
                "#........#.....#.....#..............#",
                "#...######.....#.....#..............#",
                "#..............#.....################",
                "#..............#....................#",
                "#..............#....................#",
                "#...................................#",
                "#...................................#",
                "#...................................#",
                "#####################################",
            ],
            "level3": [
                "#####################################",
                "#.....#.............................#",
                "#.....#.............................#",
                "#.....#....######....######....##...#",
                "#.....#.........#...............#...#",
                "#.....#....#....#############...#...#",
                "#.....###########...........#...#...#",
                "#.....#................#........#...#",
                "#.....#....######################...#",
                "#..........#........................#",
                "############........................#",
                "#........#...........################",
                "#...#................#..#...........#",
                "#...##################..#...........#",
                "#....................####...........#",
                "#...................................#",
                "###################################.#",
                "#..............#...#................#",
                "#..#...........#...#............#...#",
                "#..#...........#...#............#...#",
                "#..#...........#...#............#...#",
                "#..#...#########...######.......#...#",
                "#..#...#..#.............######..#...#",
                "#..#...#..#......#......#....#..#...#",
                "#..#...####......#......#....#..#...#",
                "#................#......######..#...#",
                "#...................................#",
                "#.....##########################....#",
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

                self.npcs = npcs.get(room, [])
                self.enemies = enemies.get(room, [])

        self.bug_tiles: list[tuple[int, int]] = []
        self.bug_active = False
        self.bug_spawn_interval = 1.2
        self.bug_spawn_count = 0
        self.bug_timer = None

        self.paused = False

        self.typewriter_timer = None
        self.typewriter_text = ""
        self.typewriter_index = 0
        self.typewriter_suffix = ""

    def _start_typewriter(self, text: str, suffix: str = "") -> None:
        TAG_RE = re.compile(r"\[/?[^\]]+\]")
        if self.typewriter_timer:
            self.typewriter_timer.stop()
        self.typewriter_raw = text
        self.typewriter_plain = TAG_RE.sub("", text)
        self.typewriter_index = 0
        self.typewriter_suffix = suffix
        self.typewriter_timer = self.set_interval(0.03, self._typewriter_tick)

    def _typewriter_tick(self) -> None:
        dialog = self.query_one("#dialog", Static)
        if self.typewriter_index < len(self.typewriter_plain):
            self.typewriter_index += 1
            shown = self.typewriter_plain[: self.typewriter_index]
            dialog.update(shown + self.typewriter_suffix)
        else:
            if self.typewriter_timer:
                self.typewriter_timer.stop()
                self.typewriter_timer = None
            dialog.update(self.typewriter_raw + self.typewriter_suffix)

    def _can_move(self) -> bool:
        return self.talking_to is None and not self.move_cooldown and not self.paused

    def _start_cooldown(self) -> None:
        self.move_cooldown = True
        self.set_timer(self.move_delay, self._end_cooldown)

    def _end_cooldown(self) -> None:
        self.move_cooldown = False

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(id="map")
            yield Static(id="dialog")

    def action_pause(self) -> None:
        self.paused = not self.paused
        dialog = self.query_one("#dialog", Static)
        if self.paused:
            dialog.update("[yellow]Paused - Press P to resume[/]")
        else:
            self.update_display()

    def on_mount(self) -> None:
        self.update_display()
        self.bug_timer = self.set_interval(0.4, self._spawn_bug_tiles)
        self.set_interval(0.15, self._tick_enemies)

    def update_display(self) -> None:
        if self.paused:
            self.query_one("#dialog", Static).update("[yellow]Paused[/]")
            return
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
                self._start_typewriter(
                    npc.current_line(), "\n\n[dim]Space to continue[/]"
                )
            elif self.talk_phase == TalkPhase.CHOOSING:
                text = "Choose:\n" + "\n".join(
                    f"{i + 1}. {c.label}" for i, c in enumerate(npc.choices)
                )
                dialog.update(text)
            elif self.talk_phase == TalkPhase.REPLY:
                reply = npc.choices[self.reply_index].reply if npc.choices else ""
                self._start_typewriter(reply, "\n\n[dim]Space to close[/]")
        else:
            near = any(n.is_adjacent(self.player.x, self.player.y) for n in self.npcs)
            if self.npcs and self.npcs[0].talked:
                dialog.update("[dim]Go to the exit[/]")
                if self.current_map_name == "level2":
                    self.game_map.set_tile(1, 2, "[green on green].[/]")
                    self.game_map.set_tile(2, 2, "[green on green].[/]")
            elif near:
                dialog.update("[dim]Press E to talk[/]")
            else:
                dialog.update("[dim]Approach the NPC[/]")

        # talked
        if self.npcs and self.npcs[0].talked and self.current_map_name == "init_room":
            self.game_map.set_tile(19, 5, "[green on green].[/]")
        elif (
            self.npcs
            and len(self.npcs) > 1
            and self.npcs[1].talked
            and not self.bug_active
            and self.current_map_name in ("level1", "level2")
        ):
            self.bug_active = True
            if self.current_map_name == "level1":
                self.game_map.set_tile(19, 5, "[green on green].[/]")
            elif self.current_map_name == "level2":
                if self.bug_timer:
                    self.bug_timer.stop()
                self.bug_timer = self.set_interval(1.0, self._spawn_bug_tiles)
                self.game_map.set_tile(8, 17, "[green on green].[/]")

        if (
            self.player.x == 19
            and self.player.y == 5
            and self.current_map_name == "init_room"
        ):
            self.switch_to("level1", 1, 2)

        elif (
            self.player.x == 19
            and self.player.y == 5
            and self.current_map_name == "level1"
        ):
            self.switch_to("level2", 1, 1)

        elif (
            self.player.x == 8
            and self.player.y == 17
            and self.current_map_name == "level2"
        ):
            self.switch_to("level3", 1, 1)

    def action_move_up(self) -> None:
        if self.paused:
            return
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
        if self.paused:
            return
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
        if self.paused:
            return
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
        if self.paused:
            return
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
        if self.paused:
            return
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
        if self.paused:
            return
        if self.talking_to is None:
            return
        npc = self.npcs[self.talking_to]

        if self.typewriter_timer:
            self.typewriter_timer.stop()
            self.typewriter_timer = None
            dialog = self.query_one("#dialog", Static)
            dialog.update(self.typewriter_text + self.typewriter_suffix)
            return

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

            # 重置 bug 状态
            self.bug_active = False
            self.bug_tiles.clear()
            self.bug_spawn_count = 0
            if self.bug_timer:
                self.bug_timer.stop()
                self.bug_timer = None

            self.saver.save(
                {
                    "room": map_name,
                    "player_x": player_x,
                    "player_y": player_y,
                }
            )

            self.npcs = npcs[map_name]
            self.enemies = enemies[map_name]

            self.update_display()
        else:
            self.enemies = []
            self.update_display()

    def _tick_enemies(self) -> None:
        if self.paused:
            return
        self._check_enemy_collision()
        for enemy in self.enemies:
            if isinstance(enemy, ChaserEnemy):
                enemy.update_player_pos(
                    self.player.x, self.player.y
                )  # I actually just know it work! even enemy don't have that function but ChaserEnemy do.
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
        if isinstance(enemy, SlowEnemy):
            self.move_delay = 0.3
            self.enemy_alert = "[yellow]Slowed down![/]"
            self.set_timer(2.0, self._clear_slow)
        else:
            self.enemy_alert = "Firewall: [bold red]Unauthorized Action![/]"
            self.set_timer(1.5, self._clear_enemy_alert)
            self._reset_player()

    def _clear_slow(self) -> None:
        self.move_delay = 0.06
        self.enemy_alert = None
        self.update_display()

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

    def _spawn_bug_tiles(self) -> None:
        if not self.bug_active or self.paused:
            return

        import random

        self.bug_spawn_count += 1

        if self.bug_spawn_count < 5:
            spawn_num = 1
        elif self.bug_spawn_count < 15:
            spawn_num = random.randint(1, 5)
        else:
            spawn_num = random.randint(5, 15)

        for _ in range(spawn_num):
            for _try in range(50):
                x = random.randint(1, self.game_map.width - 2)
                y = random.randint(1, self.game_map.height - 2)
                if (
                    self.game_map.is_walkable(x, y)
                    and (x, y) not in self.bug_tiles
                    and (x, y) != (self.player.x, self.player.y)
                ):
                    self.bug_tiles.append((x, y))
                    self.game_map.set_tile(x, y, "[black on black]=[/]")
                    break

        if (self.player.x, self.player.y) in self.bug_tiles:
            self.bug_active = False
            self.enemy_alert = "[bold red]U̴̥̺̝̱̿n̴̖̻͋ͪ̎ͬͦ́̔ả̴̞̫̞̮ͭ̉ͮ̽̆ͬͤu̴͈̠̰͕̝ͭ͐̈̌̇t̵̵͈̣̱͆̓̄ͥ͊̓h̶̶̎̌̐̐͋͌̏ͮo̞̪̫̦͍̞ͅŕ͔͓̼͉͔̂͊i͍͉̭̜̮̬̳z̵͖̱̬̭͎̲͕̘ͣe̼͚͚͙͈̟̙ͦ͛ͪ̔ͬ͊d̲̻͖͉̝͔̺.̮͕͌͑ͧ̈ S̤̦̠͔͇͔͓͑̓ṱ̶͍̻̦̱ͭ̐̏̆̂͒a̶̶̟̳̺͖͙ͩ̇͗̂ͫṟ̵̝̜̺̳̣͖̎͆ͧͅţ̶̱͉͈̭̼̙ͩͅ c̯̤̹͈͎̒l̸͉̗͌ͤȩ͈͇͚͔͗̍ä̪̞̮͚r̵̹̪̪̹̘̀ͧ̔ͭ͂ͨ.̸̣̞͈ͦ̽̃͑.̵̶͔ͫ̀̉.̧̧̱͆̂ͦ͑̏̍̋[/]\nPlease restart the game to start over"
            self.saver.save({})

    def _reset_player(self) -> None:
        self.player.x = 1
        self.player.y = 2
        self.enemy_alert = None
        self.update_display()


def main() -> None:
    result = StartScene().run()
    if result == "start":
        BugFinder().run()


if __name__ == "__main__":
    main()
