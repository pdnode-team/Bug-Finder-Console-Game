import pyfiglet
from textual.app import App, ComposeResult
from textual.containers import Center, Vertical
from textual.screen import ModalScreen
from textual.timer import Timer
from textual.widgets import Button, Static


class Typewriter(Static):
    def __init__(self, text: str, speed: float = 0.05) -> None:
        super().__init__()
        self.full_text = text
        self.speed = speed
        self.index = 0
        self.timer: Timer | None = None

    def on_mount(self) -> None:
        self.timer = self.set_interval(self.speed, self._type_next)

    def _type_next(self) -> None:
        if self.index < len(self.full_text):
            self.index += 1
            self.update(self.full_text[: self.index])
        else:
            if self.timer:
                self.timer.stop()


class Dialog(ModalScreen):
    DEFAULT_CSS = """
    Dialog {
        align: center middle;
    }

    #dialog {
        width: 40%;         
        height: 30%;
        min-width: 30;
        max-width: 80;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Typewriter(
                """
You wake up, dazed, to find that you’ve been transported into a black-and-white console. You have a vague recollection of participating in Hack Club’s Terra project, but you have no idea how you ended up inside this unsightly console.

A mysterious figure from beyond the scene speaks: "Welcome to '█ █ █ █ █ '—a cryptic realm that exists apart from the rest of the world. Here, you must resolve major bugs that have occurred throughout history in order to..."
                    What is “█ █ █ █ █”? Who are you?
                    You will find out. Good luck...................
                """,
                speed=0.06,
            )
            yield Button("Close", id="close")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close":
            self.dismiss(True)


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
            yield Button("Background Story", id="background")
            yield Button("Clear Data", id="clear")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start":
            self.exit("start")
        elif event.button.id == "background":
            self.push_screen(Dialog())
        elif event.button.id == "clear":
            self.query_one("#text", Static).update("Data cleared")
            from bugfinder.gamesave import GameSave

            GameSave("data.json").save({})


if __name__ == "__main__":
    StartScene().run()
