// Browser front-end for snake_model.py.
// Python (via Pyodide) owns the game state and rules; this file only
// reads input, calls tick(), and draws the snapshot it gets back.

const CELL = 36;
const TICK_MS = 110;
const SKINS = ["turquoise", "orange"];
const NAMES = ["Turquoise", "Orange"];

const canvas = document.getElementById("board");
const ctx = canvas.getContext("2d");
const ui = {
  overlay: document.getElementById("overlay"),
  title: document.getElementById("title"),
  sub: document.getElementById("sub"),
  action: document.getElementById("action"),
  s1: document.getElementById("s1"),
  s2: document.getElementById("s2"),
  best: document.getElementById("best"),
};

const BRIDGE = `
import snake_model as m

game = None

def new_game(players):
    global game
    snakes = [m.Snake.spawn("Turquoise", (4, 1))]
    if players == 2:
        snakes.append(m.Snake.spawn("Orange", (4, 3)))
    game = m.Game(snakes=snakes)
    return snapshot()

def turn(i, d):
    if i < len(game.snakes):
        game.snakes[i].turn(m.Direction[d])

def step():
    game.tick()
    return snapshot()

def snapshot():
    w = game.winner() if game.is_over and len(game.snakes) > 1 else None
    return {
        "cols": game.cols, "rows": game.rows,
        "food": list(game.food) if game.food else None,
        "over": game.is_over,
        "winner": w.name if w else None,
        "obstacles": [[r.x1, r.y1, r.x2, r.y2] for r in game.obstacles],
        "snakes": [{"body": [list(c) for c in s.body], "alive": s.alive,
                    "score": s.score, "name": s.name} for s in game.snakes],
    }
`;

let py, api, img = {}, background;
let players = 1, state = null, phase = "loading", timer = null;

// ------------------------------------------------------------------ setup
async function loadImages() {
  const names = ["apple", "grass_light", "grass_dark", "wall"];
  for (const skin of [...SKINS, "dead"]) {
    for (const d of "UDLR") names.push(`${skin}_head_${d}`, `${skin}_tail_${d}`);
    for (const p of ["UD", "UL", "UR", "DL", "DR", "LR"]) names.push(`${skin}_body_${p}`);
  }
  await Promise.all(names.map(n => new Promise((ok, fail) => {
    const i = new Image();
    i.onload = () => { img[n] = i; ok(); };
    i.onerror = () => fail(new Error(`asset ${n}`));
    i.src = `assets/${n}.png`;
  })));
}

async function boot() {
  try {
    const [pyodide, source] = await Promise.all([
      loadPyodide(),
      fetch("snake_model.py").then(r => r.text()),
      loadImages(),
    ]);
    py = pyodide;
    py.FS.writeFile("snake_model.py", source);
    py.runPython(BRIDGE);
    api = {
      newGame: py.globals.get("new_game"),
      turn: py.globals.get("turn"),
      step: py.globals.get("step"),
    };
    newGame();
  } catch (e) {
    console.error(e);
    show("Oops", "Could not start Python in this browser. Try reloading the page.");
  }
}

// --------------------------------------------------------------- game flow
const toJs = p => { const v = p.toJs({ dict_converter: Object.fromEntries }); p.destroy(); return v; };

function newGame() {
  clearTimeout(timer);
  state = toJs(api.newGame(players));
  background = null;
  render();
  phase = "ready";
  show("Snake", players === 1 ? "Eat apples, avoid walls and yourself."
                              : "Last snake alive with the most apples wins.", "Start");
}

function start() {
  if (phase !== "ready" && phase !== "over") return;
  if (phase === "over") newGame();
  countdown(3);
}

function countdown(n) {
  phase = "countdown";
  if (n === 0) { hide(); phase = "running"; loop(); return; }
  show(String(n), "Get ready…");
  timer = setTimeout(() => countdown(n - 1), 700);
}

function loop() {
  state = toJs(api.step());
  render();
  if (state.over) return gameOver();
  timer = setTimeout(loop, TICK_MS);
}

function gameOver() {
  phase = "over";
  let msg;
  if (players === 1) {
    const score = state.snakes[0].score;
    const best = Math.max(score, readBest());
    writeBest(best);
    updateHud();
    msg = `Score: ${score} · Best: ${best}`;
  } else {
    msg = state.winner ? `${state.winner} wins!` : "It's a draw!";
  }
  show("Game Over", msg, "Play again");
}

function turn(player, dir) {
  if (phase === "running" || phase === "countdown") api.turn(player, dir);
}

// ----------------------------------------------------------------- overlay
function show(title, sub, button) {
  ui.title.textContent = title;
  ui.sub.textContent = sub;
  ui.action.hidden = !button;
  if (button) ui.action.textContent = `${button} (Space)`;
  ui.overlay.hidden = false;
}
function hide() { ui.overlay.hidden = true; }

// ------------------------------------------------------------------- input
const KEYS = {
  ArrowUp: [0, "UP"], ArrowDown: [0, "DOWN"], ArrowLeft: [0, "LEFT"], ArrowRight: [0, "RIGHT"],
  w: [1, "UP"], s: [1, "DOWN"], a: [1, "LEFT"], d: [1, "RIGHT"],
};
document.addEventListener("keydown", e => {
  if (e.code === "Space") { e.preventDefault(); start(); return; }
  const k = KEYS[e.key.length === 1 ? e.key.toLowerCase() : e.key];
  if (!k) return;
  e.preventDefault();                       // keep arrows from scrolling the page
  turn(players === 1 ? 0 : k[0], k[1]);     // 1 player: arrows and WASD both work
});
ui.action.addEventListener("click", start);

document.querySelectorAll(".pad button").forEach(b =>
  b.addEventListener("pointerdown", e => { e.preventDefault(); turn(0, b.dataset.dir); }));

let touch = null;
canvas.addEventListener("touchstart", e => { touch = e.touches[0]; }, { passive: true });
canvas.addEventListener("touchend", e => {
  if (!touch) return;
  const t = e.changedTouches[0];
  const dx = t.clientX - touch.clientX, dy = t.clientY - touch.clientY;
  touch = null;
  if (Math.max(Math.abs(dx), Math.abs(dy)) < 20) return start();          // tap
  turn(0, Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? "RIGHT" : "LEFT") : (dy > 0 ? "DOWN" : "UP"));
});

document.querySelectorAll(".modes button").forEach(b => b.addEventListener("click", () => {
  document.querySelectorAll(".modes button").forEach(x => x.classList.toggle("active", x === b));
  players = Number(b.dataset.players);
  ui.s2.style.visibility = players === 2 ? "visible" : "hidden";
  b.blur();
  if (api) newGame();
}));

// -------------------------------------------------------------- high score
// Storage can be unavailable (privacy mode, sandboxed iframes): fail quietly.
function readBest() { try { return Number(localStorage.getItem("snake-best")) || 0; } catch { return 0; } }
function writeBest(v) { try { localStorage.setItem("snake-best", String(v)); } catch {} }

// --------------------------------------------------------------- rendering
const LETTER = { "0,-1": "U", "0,1": "D", "-1,0": "L", "1,0": "R" };
const OPPOSITE = { U: "D", D: "U", L: "R", R: "L" };
const side = (a, b) => LETTER[`${b[0] - a[0]},${b[1] - a[1]}`] || "R";

function drawBackground() {
  background = document.createElement("canvas");
  background.width = canvas.width; background.height = canvas.height;
  const b = background.getContext("2d");
  for (let x = 0; x < state.cols; x++)
    for (let y = 0; y < state.rows; y++)
      b.drawImage(img[(x + y) % 2 ? "grass_light" : "grass_dark"], x * CELL, y * CELL);
  for (const [x1, y1, x2, y2] of state.obstacles)
    for (let x = x1; x <= x2; x++)
      for (let y = y1; y <= y2; y++) b.drawImage(img.wall, x * CELL, y * CELL);
}

function put(name, [x, y]) { ctx.drawImage(img[name], x * CELL, y * CELL); }

function drawSnake(snake, skin) {
  skin = snake.alive ? skin : "dead";
  const body = snake.body;
  for (let i = body.length - 1; i >= 0; i--) {
    const cell = body[i];
    if (i === 0) {
      const back = body.length > 1 ? side(cell, body[1]) : "L";
      put(`${skin}_head_${OPPOSITE[back]}`, cell);
    } else if (i === body.length - 1) {
      put(`${skin}_tail_${side(cell, body[i - 1])}`, cell);
    } else {
      const pair = new Set([side(cell, body[i - 1]), side(cell, body[i + 1])]);
      put(`${skin}_body_${[..."UDLR"].filter(k => pair.has(k)).join("")}`, cell);
    }
  }
}

function updateHud() {
  const [a, b] = state.snakes;
  const label = (s, i) => `<img src="assets/apple.png" alt="">${NAMES[i]}: ${s.score}${s.alive ? "" : " ✝"}`;
  ui.s1.innerHTML = label(a, 0);
  if (b) ui.s2.innerHTML = label(b, 1);
  ui.best.textContent = players === 1 ? `Best: ${readBest()}` : "";
}

function render() {
  if (!background) drawBackground();
  ctx.drawImage(background, 0, 0);
  if (state.food) put("apple", state.food);
  state.snakes.forEach((s, i) => drawSnake(s, SKINS[i]));
  updateHud();
}

ui.s2.style.visibility = "hidden";
boot();
