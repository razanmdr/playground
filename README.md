# Playground

Small games and experiments, playable in the browser.
Live: https://razanmdr.github.io/playground/

## ♞ Chess rules engine

Movement and capture rules for all six piece types (no check/castling/promotion),
modelled with OOP pieces and a validation chain. The browser UI runs the exact
Python module via Pyodide; **Test mode** loads prepared positions and runs
`test_chess.py` in the page.

```
chess/
├── chess.py        # rules: pieces, board, validation chain, game (+ terminal CLI)
├── scenarios.py    # prepared positions for test mode
├── test_chess.py   # unit tests
├── bridge.py       # JSON-friendly functions for the browser
└── index.html, game.js   # UI: drawing and input only
```

- **One validation chain** for everything: selecting a piece runs the first three
  checks, playing a move runs all six; the failing check's name is shown as the error code.
- **Undo** keeps a board snapshot per move in `Game.history`.

## 🐍 Snake

A 1–2 player Snake. The game rules are a plain Python module; the browser
version runs that exact module through [Pyodide](https://pyodide.org)
(CPython compiled to WebAssembly), and a desktop version runs it with tkinter.

```
snake/
├── snake_model.py       # game rules: grid, movement, collisions, food (no UI)
├── test_snake_model.py  # unit tests for the rules
├── index.html, game.js  # web front-end: input + canvas drawing only
├── snake.py             # desktop front-end (tkinter)
├── make_assets.py       # generates the PNG sprites in assets/ (Pillow)
└── assets/
```

### Design notes
- **Logic separated from rendering.** `snake_model.py` knows nothing about
  canvases or keyboards, so it is testable and reused by two front-ends.
- **Simultaneous moves.** All snakes move in the same tick; collisions are
  checked against everyone's *next* position. That handles head-on crashes
  and lets a snake safely move into the cell its own tail is leaving.
- **Input buffering.** A turn is validated against the direction executed last
  tick, so two quick key presses can't reverse the snake into itself.
- **Food placement** picks from the free cells only (no walls, no snake).

### Run locally
```bash
cd snake
python -m unittest test_snake_model   # tests
python snake.py                       # desktop version (needs tkinter)
python -m http.server                 # web version → http://localhost:8000
```
