// Browser front-end for chess.py. Python owns every rule; this file only
// draws the board, forwards clicks/inputs to bridge.py and shows the answers.

const CHAIN = ["on_board", "piece_exists", "owned_by_current_player",
               "not_same_square", "not_capturing_own", "follows_piece_rules"];
const FILES = ["chess.py", "scenarios.py", "test_chess.py", "bridge.py"];

const $ = id => document.getElementById(id);
let py, api, view = null, selected = null, targets = [], hints = true;

// ------------------------------------------------------------------ pieces
const PATHS = {
  RK: `<path d="M9 39h27v-3H9v3zM12 36v-4h21v4H12zM11 14V9h4v2h5V9h5v2h5V9h4v5"/><path d="M34 14l-3 3H14l-3-3"/><path d="M31 17v12.5H14V17"/><path d="M31 29.5l1.5 2.5h-20l1.5-2.5"/><path d="M11 14h23" fill="none"/>`,
  KN: `<path d="M22,10 C32.5,11 38.5,18 38,39 L15,39 C15,30 25,32.5 23,18"/><path d="M24,18 C24.38,20.91 18.45,25.37 16,27 C13,29 13.18,31.34 11,31 C9.958,30.06 12.41,27.96 11,28 C10,28 11.19,29.23 10,30 C9,30 5.997,31 6,26 C6,24 12,14 12,14 C12,14 13.89,12.1 14,10.5 C13.27,9.506 13.5,8.5 13.5,7.5 C14.5,6.5 16.5,10 16.5,10 L18.5,10 C18.5,10 19.28,8.008 21,7 C22,7 22,10 22,10"/><circle cx="14.5" cy="15.5" r="1" fill="currentColor"/>`,
  BS: `<path d="M9 36c3.39-.97 10.11.43 13.5-2 3.39 2.43 10.11 1.03 13.5 2 0 0 1.65.54 3 2-.68.97-1.65.99-3 .5-3.39-.97-10.11.46-13.5-1-3.39 1.46-10.11.03-13.5 1-1.35.49-2.32.47-3-.5 1.35-1.94 3-2 3-2z"/><path d="M15 32c2.5 2.5 12.5 2.5 15 0 .5-1.5 0-2 0-2 0-2.5-2.5-4-2.5-4 5.5-1.5 6-11.5-5-15.5-11 4-10.5 14-5 15.5 0 0-2.5 1.5-2.5 4 0 0-.5.5 0 2z"/><circle cx="22.5" cy="8" r="2.5"/><path d="M17.5 26h10M15 30h15m-7.5-14.5v5M20 18h5" fill="none"/>`,
  QU: `<circle cx="6" cy="12" r="2"/><circle cx="14" cy="9" r="2"/><circle cx="22.5" cy="8" r="2"/><circle cx="31" cy="9" r="2"/><circle cx="39" cy="12" r="2"/><path d="M9 26c8.5-1.5 21-1.5 27 0l2-12-7 11V11l-5.5 13.5-3-15-3 15-5.5-14V25L7 14l2 12z"/><path d="M9 26c0 2 1.5 2 2.5 4 1 1.5 1 1 .5 3.5-1.5 1-1.5 2.5-1.5 2.5-1.5 1.5.5 2.5.5 2.5 6.5 1 16.5 1 23 0 0 0 1.5-1 0-2.5 0 0 .5-1.5-1-2.5-.5-2.5-.5-2 .5-3.5 1-2 2.5-2 2.5-4-8.5-1.5-18.5-1.5-27 0z"/><path d="M11.5 30c3.5-1 18.5-1 22 0M12 33.5c6-1 15-1 21 0" fill="none"/>`,
  KI: `<path d="M22.5 11.63V6M20 8h5" fill="none"/><path d="M22.5 25s4.5-7.5 3-10.5c0 0-1-2.5-3-2.5s-3 2.5-3 2.5c-1.5 3 3 10.5 3 10.5"/><path d="M11.5 37c5.5 3.5 15.5 3.5 21 0v-7s9-4.5 6-10.5c-4-6.5-13.5-3.5-16 4V27v-3.5c-3.5-7.5-13-10.5-16-4-3 6 5 10 5 10V37z"/><path d="M11.5 30c5.5-3 15.5-3 21 0m-21 3.5c5.5-3 15.5-3 21 0m-21 3.5c5.5-3 15.5-3 21 0" fill="none"/>`,
  PW: `<path d="M22.5 9c-2.21 0-4 1.79-4 4 0 .89.29 1.71.78 2.38C17.33 16.5 16 18.59 16 21c0 2.03.94 3.84 2.41 5.03-3 1.06-7.41 5.55-7.41 13.47h23c0-7.92-4.41-12.41-7.41-13.47 1.47-1.19 2.41-3 2.41-5.03 0-2.41-1.33-4.5-3.28-5.62.49-.67.78-1.49.78-2.38 0-2.21-1.79-4-4-4z"/>`,
};
function pieceSvg(code) {
  const white = code === code.toUpperCase();
  const [fill, stroke] = white ? ["#F4F7FB", "#0B1120"] : ["#101A2C", "#E8EEF8"];
  return `<svg viewBox="0 0 45 45"><g fill="${fill}" stroke="${stroke}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">${PATHS[code.toUpperCase()]}</g></svg>`;
}

// ------------------------------------------------------------------- sound
// Four short blips don't need an audio library: plain Web Audio is enough.
const sound = {
  on: true, ctx: null,
  blip(freqs, dur = 0.09, type = "triangle") {
    if (!this.on) return;
    try {
      this.ctx ??= new (window.AudioContext || window.webkitAudioContext)();
      if (this.ctx.state === "suspended") this.ctx.resume();
      const t = this.ctx.currentTime;
      for (const f of freqs) {
        const o = this.ctx.createOscillator(), g = this.ctx.createGain();
        o.type = type; o.frequency.value = f;
        g.gain.setValueAtTime(0.08, t); g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
        o.connect(g).connect(this.ctx.destination); o.start(t); o.stop(t + dur);
      }
    } catch { /* audio is optional */ }
  },
  select() { this.blip([523]); }, move() { this.blip([330, 392]); },
  capture() { this.blip([262, 370, 440], 0.14); }, error() { this.blip([98, 104], 0.16, "square"); },
};

// ------------------------------------------------------------------- python
const call = (fn, ...args) => {
  const r = api[fn](...args);
  if (r && typeof r.toJs === "function") { const v = r.toJs({ dict_converter: Object.fromEntries }); r.destroy(); return v; }
  return r;
};

async function boot() {
  try {
    const [pyodide, ...sources] = await Promise.all([
      loadPyodide(), ...FILES.map(f => fetch(f).then(r => { if (!r.ok) throw new Error(f); return r.text(); })),
    ]);
    py = pyodide;
    FILES.forEach((f, i) => py.FS.writeFile(f, sources[i]));
    const bridge = py.pyimport("bridge");
    api = Object.fromEntries(["new_game", "scenarios", "select", "play", "play_text", "undo", "state", "run_tests"]
      .map(n => [n, bridge[n]]));
    $("loading").remove();
    buildBoard();
    renderScenarios();
    newGame("standard");
  } catch (e) {
    console.error(e);
    $("loading").textContent = "Could not start Python in this browser. Try reloading.";
  }
}

// ---------------------------------------------------------------- game flow
function newGame(key) {
  view = call("new_game", key);
  clearSelection();
  render();
  message("Click a white piece, then a target square.", "");
  chain(null);
}

function clearSelection() { selected = null; targets = []; }

function clickSquare(r, c) {
  if (selected) {
    if (selected[0] === r && selected[1] === c) { clearSelection(); render(); return; }
    const own = view.rows[r][c] !== "--" && isTurnPiece(view.rows[r][c]);
    if (!own) return tryMove(selected, [r, c]);
  }
  const res = call("select", r, c);
  if (!res.ok) { fail(res, [r, c]); return; }
  selected = [r, c]; targets = res.targets;
  sound.select();
  message(`${res.piece} on (${r}, ${c}) selected: ${targets.length} legal ${targets.length === 1 ? "move" : "moves"}.`, "");
  chain(null);
  render();
}

const isTurnPiece = code => (code === code.toUpperCase()) === (view.turn === "White");

function tryMove(src, dst, viaText) {
  const res = viaText ? call("play_text", ...viaText) : call("play", src, dst);
  if (!res.ok) { fail(res, dst); return false; }
  view = call("state");
  clearSelection();
  chain("all");
  if (res.captured) { sound.capture(); message(`${res.piece} captures ${res.captured}.`, "capture"); }
  else { sound.move(); message(`${res.piece} moved. ${view.turn} to move.`, "ok"); }
  render();
  return true;
}

function fail(res, square) {
  sound.error();
  message(res.error, "error");
  chain(res.code);
  if (square && square[0] >= 0 && square[0] < 8 && square[1] >= 0 && square[1] < 8) {
    const el = $("board").children[square[0] * 8 + square[1]];
    el.classList.remove("shake"); void el.offsetWidth; el.classList.add("shake");
  }
}

// ------------------------------------------------------------------ render
function buildBoard() {
  const board = $("board");
  for (let r = 0; r < 8; r++) for (let c = 0; c < 8; c++) {
    const b = document.createElement("button");
    b.className = `sq ${(r + c) % 2 ? "d" : "l"}`;
    b.setAttribute("aria-label", `row ${r}, column ${c}`);
    b.addEventListener("click", () => clickSquare(r, c));
    board.appendChild(b);
  }
  $("ranks").innerHTML = [...Array(8).keys()].map(i => `<span>${i}</span>`).join("");
  $("files").innerHTML = [...Array(8).keys()].map(i => `<span>${i}</span>`).join("");
}

function render() {
  const squares = $("board").children;
  const [lastSrc, lastDst] = view.last || [[-1, -1], [-1, -1]];
  for (let r = 0; r < 8; r++) for (let c = 0; c < 8; c++) {
    const el = squares[r * 8 + c], code = view.rows[r][c];
    const t = hints && targets.find(([tr, tc]) => tr === r && tc === c);
    el.classList.toggle("sel", !!selected && selected[0] === r && selected[1] === c);
    el.classList.toggle("last", (r === lastSrc[0] && c === lastSrc[1]) || (r === lastDst[0] && c === lastDst[1]));
    el.classList.toggle("target", !!t && !t[2]);
    el.classList.toggle("capture", !!t && t[2]);
    el.innerHTML = code === "--" ? "" : pieceSvg(code);
  }
  $("turn").textContent = `${view.turn} to move`;
  $("turn-dot").className = `dot ${view.turn}`;
  $("undo").disabled = view.history.length === 0;

  const capW = view.captured.White, capB = view.captured.Black;
  $("cnt-w").textContent = capW.length; $("cnt-b").textContent = capB.length;
  $("cap-w").innerHTML = capW.length ? capW.map(pieceSvg).join("") : '<span class="empty">none yet</span>';
  $("cap-b").innerHTML = capB.length ? capB.map(pieceSvg).join("") : '<span class="empty">none yet</span>';

  const h = $("history");
  h.innerHTML = view.history.length ? view.history.map((m, i) =>
    `<div><span>${String(i + 1).padStart(2, " ")}.</span><b>${m.code}</b><span>${m.src.join(" ")} → ${m.dst.join(" ")}</span>${m.captured ? `<span class="x">× ${m.captured}</span>` : ""}</div>`
  ).join("") : '<span class="empty">No moves yet.</span>';
  h.scrollTop = h.scrollHeight;
}

function message(text, kind) { const m = $("msg"); m.textContent = text; m.className = kind; }

/** Show the validation chain: which checks passed and which one stopped the move. */
function chain(failed) {
  $("chain").innerHTML = CHAIN.map((name, i) => {
    let cls = "";
    if (failed === "all") cls = "pass";
    else if (failed && CHAIN.includes(failed)) cls = i < CHAIN.indexOf(failed) ? "pass" : i === CHAIN.indexOf(failed) ? "fail" : "";
    return `<span class="${cls}">${i + 1}. ${name}</span>`;
  }).join("") + (failed === "parse_position" ? '<span class="fail">parse_position</span>' : "");
}

// --------------------------------------------------------------- test mode
function renderScenarios() {
  $("scenarios").innerHTML = call("scenarios").map(s =>
    `<button class="scn" data-key="${s.key}"><b>${s.title}</b><small>${s.text}</small></button>`).join("");
  $("scenarios").querySelectorAll(".scn").forEach(b => b.addEventListener("click", () => {
    newGame(b.dataset.key);
    message(`Scenario loaded: ${b.querySelector("b").textContent}. White to move.`, "ok");
    $("dlg").close();
  }));
}

$("run-tests").addEventListener("click", () => {
  $("test-summary").textContent = "Running…";
  setTimeout(() => {
    const r = call("run_tests");
    $("test-summary").innerHTML = `<span style="color:${r.ok ? "var(--prompt)" : "var(--error)"}">${r.ok ? "✔" : "✘"} ${r.ran} tests ${r.ok ? "passed" : "— some failed"}</span>`;
    $("tests").innerHTML = r.tests.map(([name, st]) => `<div><span>${name}</span><span class="${st}">${st}</span></div>`).join("");
  }, 20);
});

// ------------------------------------------------------------------ inputs
$("cli").addEventListener("submit", e => {
  e.preventDefault();
  if (tryMove(null, null, [$("cli-src").value, $("cli-dst").value])) { $("cli-src").value = ""; $("cli-dst").value = ""; }
});
$("undo").addEventListener("click", () => {
  if (call("undo").ok) { view = call("state"); clearSelection(); chain(null); sound.select(); message(`Move undone. ${view.turn} to move.`, ""); render(); }
});
$("reset").addEventListener("click", () => { newGame("standard"); sound.move(); });
$("testmode").addEventListener("click", () => $("dlg").showModal());
$("dlg-close").addEventListener("click", () => $("dlg").close());
$("hints").addEventListener("click", e => { hints = !hints; e.currentTarget.classList.toggle("on", hints); render(); });
$("sound").addEventListener("click", e => { sound.on = !sound.on; e.currentTarget.classList.toggle("on", sound.on); if (sound.on) sound.select(); });

boot();
