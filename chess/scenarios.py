"""Ready-made positions for the playground's test mode (also used by the tests)."""
from chess import Board

SCENARIOS = {
    "standard": ("Standard position", "All 32 pieces, White to move.", None),
    "sliding": ("Sliding pieces & blocking", "Rook, Bishop and Queen; pieces in the way stop them.", [
        "-- -- -- -- ki -- -- --",
        "-- -- -- -- -- -- -- --",
        "pw -- -- -- -- -- -- rk",
        "-- -- -- -- -- -- -- --",
        "-- -- -- -- KI -- -- --",
        "-- -- -- -- -- -- -- --",
        "-- -- -- -- -- -- -- --",
        "RK -- BS QU -- -- -- --",
    ]),
    "pawns": ("Pawn pushes & captures", "Double step from the start row, blocked pushes, diagonal captures.", [
        "-- -- -- -- ki -- -- --",
        "-- -- -- -- -- -- -- --",
        "-- -- -- -- -- -- -- --",
        "-- -- -- rk pw -- -- --",
        "-- -- -- PW -- -- -- --",
        "-- -- -- -- -- -- -- --",
        "-- -- -- -- PW -- -- --",
        "-- -- -- -- KI -- -- --",
    ]),
    "knight": ("Knight jumps", "A Knight boxed in by its own pawns can still jump.", [
        "-- -- -- -- ki -- -- --",
        "-- -- -- -- -- -- -- --",
        "-- -- -- rk -- -- -- --",
        "-- -- -- PW PW PW -- --",
        "-- -- -- PW KN PW -- --",
        "-- -- -- PW PW PW -- --",
        "-- -- -- -- -- -- -- --",
        "-- -- -- -- KI -- -- --",
    ]),
}


def board_for(key: str) -> Board:
    rows = SCENARIOS[key][2]
    return Board.standard() if rows is None else Board.from_rows(rows)
