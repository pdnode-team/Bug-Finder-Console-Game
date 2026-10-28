from __future__ import annotations

from textual.app import App, ComposeResult
from textual.widgets import Static
from textual.containers import Vertical
from textual.binding import Binding

class BugFinder(App[None]):
    CSS = """
    #map {
        height: 1fr;
        border: solid gray;
    }
    #dialog {
        height: 8;
        border: solid gray;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("w", "move_up", "Up"),
        Binding("s", "move_down", "Down"),
        Binding("a", "move_left", "Left"),
        Binding("d", "move_right", "Right"),
        Binding("e", "talk", "Talk"),
        Binding("space", "continue_dialog", "Continue"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.map: list[str] = [
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
        ]
        self.player_x: int = 2
        self.player_y: int = 2
        self.npc_x: int = 12
        self.npc_y: int = 5
        self.dialog_lines: list[str] = [
                "Hello!",
                "Welcome to ██████",
                "This place is very old and fragile",
                "If you want to escape...",
                "You can look for bugs and reduce \"system stability\"",
                "Remember, the lower the system stability, the greater the danger you're in"
            ]
        self.dialog_index: int = 0
        self.talking: bool = False

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Static(id="map")
            yield Static(id="dialog")

    def on_mount(self) -> None:
        self.update_display()

    def update_display(self) -> None:
        lines: list[str] = []
        for y, row in enumerate(self.map):
            line = ""
            for x, ch in enumerate(row):
                if x == self.player_x and y == self.player_y:
                    line += "@"
                elif x == self.npc_x and y == self.npc_y:
                    line += "H"
                else:
                    line += ch
            lines.append(line)

        map_widget = self.query_one("#map", Static)
        map_widget.update("\n".join(lines))

        dialog_widget = self.query_one("#dialog", Static)
        if self.talking:
            text = self.dialog_lines[self.dialog_index]
            dialog_widget.update(f"[yellow]{text}[/]\n\n[dim]Space to continue[/]")
        else:
            near = abs(self.player_x - self.npc_x) <= 1 and abs(self.player_y - self.npc_y) <= 1
            hint = "Press E to talk" if near else "Approach the NPC"
            dialog_widget.update(f"[dim]{hint}[/]")

    def action_move_up(self) -> None:
        if not self.talking and self.player_y > 1:
            self.player_y -= 1
            self.update_display()

    def action_move_down(self) -> None:
        if not self.talking and self.player_y < len(self.map) - 2:
            self.player_y += 1
            self.update_display()

    def action_move_left(self) -> None:
        if not self.talking and self.player_x > 1:
            self.player_x -= 1
            self.update_display()

    def action_move_right(self) -> None:
        if not self.talking and self.player_x < len(self.map[0]) - 2:
            self.player_x += 1
            self.update_display()

    def action_talk(self) -> None:
        if self.talking:
            return
        dx = abs(self.player_x - self.npc_x)
        dy = abs(self.player_y - self.npc_y)
        if dx <= 1 and dy <= 1 and not (dx == 0 and dy == 0):
            self.talking = True
            self.dialog_index = 0
            self.update_display()

    def action_continue_dialog(self) -> None:
        if not self.talking:
            return
        self.dialog_index += 1
        if self.dialog_index >= len(self.dialog_lines):
            self.talking = False
            self.dialog_index = 0
        self.update_display()

    async def action_quit(self) -> None:
        self.exit()

if __name__ == "__main__":
    BugFinder().run()