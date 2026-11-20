# Playground

Small games and experiments, playable in the browser.
Live: https://razanmdr.github.io/playground/

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
