"""Thin JSON-friendly layer between the browser UI (game.js) and chess.py."""
import io
import unittest

import chess as ch
import scenarios as sc

game = ch.Game()


def _pos(pair):
    return ch.Position(int(pair[0]), int(pair[1]))


def _error(e):
    return {"ok": False, "error": str(e), "code": getattr(e, "code", "parse_position")}


def new_game(key="standard"):
    global game
    game = ch.Game(sc.board_for(key))
    return state()


def scenarios():
    return [{"key": k, "title": t, "text": d} for k, (t, d, _) in sc.SCENARIOS.items()]


def select(row, col):
    """Validate a selection with the same chain the moves use; return legal targets."""
    pos = ch.Position(row, col)
    try:
        game.validate_selection(pos)
    except ch.InvalidMove as e:
        return _error(e)
    piece = game.board.get(pos)
    targets = [[p.row, p.col, game.board.get(p) is not None] for p in game.legal_destinations(pos)]
    return {"ok": True, "piece": piece.name, "code": str(piece), "targets": targets}


def play(src, dst):
    try:
        move = ch.Move(_pos(src), _pos(dst))
        piece = game.board.get(move.src) if move.src.is_on_board() else None
        captured = game.play(move)
    except ch.InvalidMove as e:
        return _error(e)
    return {"ok": True, "piece": piece.name, "captured": captured.name if captured else None}


def play_text(src_text, dst_text):
    """CLI-style input, parsed by the same parse_position the terminal version uses."""
    try:
        src, dst = ch.parse_position(src_text), ch.parse_position(dst_text)
    except ValueError as e:
        return _error(e)
    return play([src.row, src.col], [dst.row, dst.col])


def undo():
    return {"ok": game.undo()}


def state():
    return {
        "rows": game.board.rows(),
        "turn": game.turn.value,
        "history": [{
            "color": t.piece.color.value, "code": str(t.piece),
            "src": [t.move.src.row, t.move.src.col], "dst": [t.move.dst.row, t.move.dst.col],
            "captured": str(t.captured) if t.captured else None,
        } for t in game.history],
        "captured": {c.value: [str(p) for p in game.captured_by(c)] for c in ch.Color},
        "last": ([[t.move.src.row, t.move.src.col], [t.move.dst.row, t.move.dst.col]]
                 if (t := game.history[-1] if game.history else None) else None),
    }


class _Collector(unittest.TextTestResult):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.rows = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.rows.append([test.id().split(".", 1)[1], "ok"])

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.rows.append([test.id().split(".", 1)[1], "fail"])

    def addError(self, test, err):
        super().addError(test, err)
        self.rows.append([test.id().split(".", 1)[1], "error"])


def run_tests():
    """Run the real test_chess.py inside the browser and report each test."""
    suite = unittest.defaultTestLoader.loadTestsFromName("test_chess")
    runner = unittest.TextTestRunner(stream=io.StringIO(), resultclass=_Collector, verbosity=0)
    result = runner.run(suite)
    return {"ran": result.testsRun, "ok": result.wasSuccessful(), "tests": result.rows}
