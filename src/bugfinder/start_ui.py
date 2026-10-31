import pyfiglet
from textual.app import App, ComposeResult
from textual.containers import Center, Vertical
from textual.widgets import Button, Static


class StartScene(App):
    # Imagine using CSS in CLI lol

    CSS = """
    Screen {
        align: center middle;
    }
    #title {
        text-align: center;
        color: cyan;
    }
    #author {
        text-align: center;
        margin-bottom: 2;
    }
    #box {
        width: 60;
        height: auto;
    }
    Button {
        width: 100%;
        margin: 1 0;
    }
    """

    def compose(self) -> ComposeResult:
        big_title = pyfiglet.figlet_format("Bug Finder", font="slant")
        with Center(), Vertical(id="box"):
            yield Static(big_title, id="title")
            yield Static("By Pidan", id="author")
            yield Static("", id="text")
            yield Button("Start Game", id="start")
            yield Button("Clear Data", id="clear")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start":
            self.exit("start")
        elif event.button.id == "clear":
            self.query_one("#text", Static).update("Data cleared")
            from bugfinder.gamesave import GameSave

            GameSave("data.json").save({})


if __name__ == "__main__":
    StartScene().run()
