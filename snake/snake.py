"""
Two-player Snake (tkinter view with PNG sprites from ./assets).

Spieler 1 (Türkis): Pfeiltasten   |   Spieler 2 (Orange): W A S D
Leertaste: Neustart nach Game Over
"""
import tkinter as tk
from pathlib import Path

from snake_model import COLS, ROWS, Direction, Game

CELL = 36                 # must match the sprite size in make_assets.py
HUD = 56                  # height of the score bar above the board
TICK_MS = 110
ASSETS = Path(__file__).parent / "assets"

SKINS = ["turquoise", "orange"]
TEXT_COLORS = ["#7ff0e6", "#ffc070"]
CONTROLS = [
    {"Up": Direction.UP, "Down": Direction.DOWN, "Left": Direction.LEFT, "Right": Direction.RIGHT},
    {"w": Direction.UP, "s": Direction.DOWN, "a": Direction.LEFT, "d": Direction.RIGHT},
]
FONT = "Helvetica"


def direction_letter(a, b) -> str:
    """Letter (U/D/L/R) of the side of cell a that touches neighbour b."""
    return {(0, -1): "U", (0, 1): "D", (-1, 0): "L", (1, 0): "R"}.get(
        (b[0] - a[0], b[1] - a[1]), "R")


class SnakeApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title("Snake")
        root.resizable(False, False)
        self.width, self.height = COLS * CELL, ROWS * CELL + HUD
        self.canvas = tk.Canvas(root, width=self.width, height=self.height,
                                bg="#4a752c", highlightthickness=0)
        self.canvas.pack()
        root.bind("<KeyPress>", self.on_key)

        # Keep references, otherwise Tk garbage-collects the images.
        self.img = {p.stem: tk.PhotoImage(file=p) for p in ASSETS.glob("*.png")}
        self.img["apple_small"] = self.img["apple"].subsample(2)

        self.game: Game
        self.running = False
        self.new_game()

    # ------------------------------------------------------------ game flow
    def new_game(self) -> None:
        self.game = Game()
        self.running = False
        self.draw_static()
        self.render()
        self.countdown(3)

    def countdown(self, n: int) -> None:
        if n:
            self.render(title=str(n), subtitle="Türkis: Pfeiltasten   ·   Orange: W A S D")
            self.root.after(800, self.countdown, n - 1)    # non-blocking
        else:
            self.running = True
            self.loop()

    def loop(self) -> None:
        if not self.running:
            return
        self.game.tick()
        if self.game.is_over:
            self.running = False
            w = self.game.winner()
            msg = f"{w.name} gewinnt!" if w else "Unentschieden!"
            self.render(title="Game Over", subtitle=f"{msg}\nLeertaste = Neustart")
            return
        self.render()
        self.root.after(TICK_MS, self.loop)

    def on_key(self, event: tk.Event) -> None:
        if event.keysym == "space" and self.game.is_over:
            self.new_game()
            return
        key = event.keysym if event.keysym in ("Up", "Down", "Left", "Right") \
            else event.keysym.lower()                       # Caps Lock safe
        for snake, mapping in zip(self.game.snakes, CONTROLS):
            if key in mapping:
                snake.turn(mapping[key])

    # ------------------------------------------------------------ rendering
    def xy(self, cell):
        return cell[0] * CELL, cell[1] * CELL + HUD

    def put(self, name, cell, tag="dynamic"):
        self.canvas.create_image(*self.xy(cell), image=self.img[name], anchor="nw", tags=tag)

    def draw_static(self) -> None:
        """Grass and walls never change: draw once per game, not every tick."""
        self.canvas.delete("all")
        for x in range(COLS):
            for y in range(ROWS):
                self.put("grass_light" if (x + y) % 2 else "grass_dark", (x, y), "static")
        for r in self.game.obstacles:
            for cell in r.cells():
                self.put("wall", cell, "static")

    def draw_snake(self, snake, skin) -> None:
        skin = skin if snake.alive else "dead"
        body = snake.body
        for i in range(len(body) - 1, -1, -1):              # tail first, head on top
            cell = body[i]
            if i == 0:
                back = direction_letter(cell, body[1]) if len(body) > 1 else "L"
                facing = {"U": "D", "D": "U", "L": "R", "R": "L"}[back]
                self.put(f"{skin}_head_{facing}", cell)
            elif i == len(body) - 1:
                self.put(f"{skin}_tail_{direction_letter(cell, body[i - 1])}", cell)
            else:
                pair = {direction_letter(cell, body[i - 1]), direction_letter(cell, body[i + 1])}
                key = "".join(k for k in "UDLR" if k in pair)
                self.put(f"{skin}_body_{key}", cell)

    def draw_hud(self) -> None:
        cv = self.canvas
        cv.create_rectangle(0, 0, self.width, HUD, fill="#4a752c", outline="", tags="dynamic")
        for i, (snake, color) in enumerate(zip(self.game.snakes, TEXT_COLORS)):
            left = i == 0
            x = 24 if left else self.width - 24
            cv.create_image(x, HUD / 2, image=self.img["apple_small"],
                            anchor="w" if left else "e", tags="dynamic")
            tx = x + 28 if left else x - 28
            status = "" if snake.alive else "  ✝"
            cv.create_text(tx, HUD / 2, text=f"{snake.name}: {snake.score}{status}",
                           fill=color, anchor="w" if left else "e",
                           font=(FONT, 18, "bold"), tags="dynamic")
        cv.create_text(self.width / 2, HUD / 2, text="SNAKE", fill="white",
                       font=(FONT, 20, "bold"), tags="dynamic")

    def draw_overlay(self, title, subtitle) -> None:
        cx, cy = self.width / 2, HUD + ROWS * CELL / 2
        cv = self.canvas
        cv.create_image(cx, cy, image=self.img["panel"], tags="dynamic")
        cv.create_text(cx, cy - 40, text=title, fill="white",
                       font=(FONT, 48, "bold"), tags="dynamic")
        cv.create_text(cx, cy + 50, text=subtitle, fill="#e8f5d0", justify="center",
                       font=(FONT, 18), tags="dynamic")

    def render(self, title: str | None = None, subtitle: str = "") -> None:
        self.canvas.delete("dynamic")                       # static layer stays
        if self.game.food:
            self.put("apple", self.game.food)
        for snake, skin in zip(self.game.snakes, SKINS):
            self.draw_snake(snake, skin)
        self.draw_hud()
        if title:
            self.draw_overlay(title, subtitle)


def main() -> None:
    root = tk.Tk()
    SnakeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
