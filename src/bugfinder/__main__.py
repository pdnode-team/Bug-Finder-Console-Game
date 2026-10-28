from __future__ import annotations

from textual.app import App, ComposeResult
from textual.widgets import Static
from textual.containers import Vertical
from textual.binding import Binding

from .map import GameMap
from .player import Player
from .npc import Npc, Choice

class TalkPhase:
    LINES = "lines"
    CHOOSING = "choosing"
    REPLY = "reply"

class BugFinder(App[None]):
    CSS = """
    #map { height: 1fr; border: solid gray; }
    #dialog { height: 8; border: solid gray; }
    """

    BINDINGS = [
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
        self.game_map = GameMap([
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
        ])
        self.player = Player(2, 2)
        self.npcs = [
            Npc(
                "H", 12, 5,
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
        ]
        self.talking_to: int | None = None
        self.talk_phase = TalkPhase.LINES
        self.reply_index = 0

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(id="map")
            yield Static(id="dialog")

    def on_mount(self) -> None:
        self.update_display()

    def update_display(self) -> None:
        map_text = self.game_map.render(self.player.x, self.player.y, self.npcs)
        self.query_one("#map", Static).update(map_text)

        dialog = self.query_one("#dialog", Static)
        if self.talking_to is not None:
            npc = self.npcs[self.talking_to]
            if self.talk_phase == TalkPhase.LINES:
                dialog.update(f"[yellow]{npc.current_line()}[/]\n\n[dim]Space to continue[/]")
            elif self.talk_phase == TalkPhase.CHOOSING:
                text = "Choose:\n" + "\n".join(f"{i+1}. {c.label}" for i, c in enumerate(npc.choices))
                dialog.update(text)
            elif self.talk_phase == TalkPhase.REPLY:
                reply = npc.choices[self.reply_index].reply if npc.choices else ""
                dialog.update(f"[yellow]{reply}[/]\n\n[dim]Space to close[/]")
        else:
            near = any(n.is_adjacent(self.player.x, self.player.y) for n in self.npcs)
            if self.npcs and self.npcs[0].talked: dialog.update("[dim]Go to the exit[/]")
            elif near: dialog.update("[dim]Press E to talk[/]")
            else: dialog.update("[dim]Approach the NPC[/]")

        # talked
        if self.npcs and self.npcs[0].talked:
            self.game_map.set_tile(19, 5, "[green on green].[/]")


    def action_move_up(self) -> None:
        if self.talking_to is None:
            self.player.try_move(0, -1, self.game_map)
            self.update_display()

    def action_move_down(self) -> None:
        if self.talking_to is None:
            self.player.try_move(0, 1, self.game_map)
            self.update_display()

    def action_move_left(self) -> None:
        if self.talking_to is None:
            self.player.try_move(-1, 0, self.game_map)
            self.update_display()

    def action_move_right(self) -> None:
        if self.talking_to is None:
            self.player.try_move(1, 0, self.game_map)
            self.update_display()

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

def main() -> None:
    BugFinder().run()

if __name__ == "__main__":
    main()