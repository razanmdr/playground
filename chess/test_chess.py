import unittest
from chess import (Board, Bishop, Color, Game, InvalidMove, King, Knight,
                   Move, Pawn, Position, Queen, Rook)


def m(r1, c1, r2, c2):
    return Move(Position(r1, c1), Position(r2, c2))


def empty_game(*placements, turn=Color.WHITE):
    """Game on an empty board with given (row, col, piece) placements."""
    board = Board()
    for r, c, piece in placements:
        board.set(Position(r, c), piece)
    game = Game(board)
    game.turn = turn
    return game


class TestValidationChain(unittest.TestCase):
    def setUp(self):
        self.game = Game()

    def test_empty_square(self):
        with self.assertRaisesRegex(InvalidMove, "no piece"):
            self.game.play(m(4, 4, 3, 4))

    def test_wrong_turn(self):
        with self.assertRaisesRegex(InvalidMove, "does not belong"):
            self.game.play(m(1, 4, 2, 4))

    def test_off_board(self):
        with self.assertRaisesRegex(InvalidMove, "between 0 and 7"):
            self.game.play(m(6, 4, 8, 4))

    def test_capture_own(self):
        with self.assertRaisesRegex(InvalidMove, "own piece"):
            self.game.play(m(7, 0, 6, 0))

    def test_turn_switches(self):
        self.game.play(m(6, 4, 4, 4))
        self.assertIs(self.game.turn, Color.BLACK)


class TestPawn(unittest.TestCase):
    def test_single_and_double_push_from_start(self):
        g = Game()
        g.play(m(6, 4, 4, 4))   # white double
        g.play(m(1, 3, 2, 3))   # black single

    def test_no_double_after_first_move(self):
        g = empty_game((5, 4, Pawn(Color.WHITE)))
        with self.assertRaises(InvalidMove):
            g.play(m(5, 4, 3, 4))

    def test_no_backwards(self):
        g = empty_game((4, 4, Pawn(Color.WHITE)))
        with self.assertRaises(InvalidMove):
            g.play(m(4, 4, 5, 4))

    def test_blocked_forward(self):
        g = empty_game((6, 4, Pawn(Color.WHITE)), (5, 4, Pawn(Color.BLACK)))
        with self.assertRaises(InvalidMove):
            g.play(m(6, 4, 5, 4))
        with self.assertRaises(InvalidMove):
            g.play(m(6, 4, 4, 4))  # jumping over

    def test_diagonal_capture_only(self):
        g = empty_game((4, 4, Pawn(Color.WHITE)), (3, 5, Pawn(Color.BLACK)))
        with self.assertRaises(InvalidMove):
            g.play(m(4, 4, 3, 3))  # diagonal to empty square
        captured = g.play(m(4, 4, 3, 5))
        self.assertIsInstance(captured, Pawn)


class TestSlidingPieces(unittest.TestCase):
    def test_rook(self):
        g = empty_game((7, 0, Rook(Color.WHITE)))
        g.play(m(7, 0, 0, 0))
        g = empty_game((7, 0, Rook(Color.WHITE)))
        with self.assertRaises(InvalidMove):
            g.play(m(7, 0, 5, 2))

    def test_bishop(self):
        g = empty_game((7, 2, Bishop(Color.WHITE)))
        g.play(m(7, 2, 2, 7))
        g = empty_game((7, 2, Bishop(Color.WHITE)))
        with self.assertRaises(InvalidMove):
            g.play(m(7, 2, 5, 2))

    def test_queen(self):
        for dst in [(0, 3), (7, 0), (4, 0), (3, 7)]:
            g = empty_game((7, 3, Queen(Color.WHITE)))
            g.play(m(7, 3, *dst))
        g = empty_game((7, 3, Queen(Color.WHITE)))
        with self.assertRaises(InvalidMove):
            g.play(m(7, 3, 5, 4))  # L-shape

    def test_blocked_path(self):
        g = Game()  # standard: rook boxed in by own pawn
        with self.assertRaises(InvalidMove):
            g.play(m(7, 0, 4, 0))

    def test_capture_at_end_of_path(self):
        g = empty_game((7, 0, Rook(Color.WHITE)), (2, 0, Pawn(Color.BLACK)))
        self.assertIsInstance(g.play(m(7, 0, 2, 0)), Pawn)


class TestKnightAndKing(unittest.TestCase):
    def test_knight_jumps_over_pieces(self):
        g = Game()
        g.play(m(7, 1, 5, 2))

    def test_knight_invalid_shape(self):
        g = Game()
        with self.assertRaises(InvalidMove):
            g.play(m(7, 1, 5, 1))

    def test_king_one_step(self):
        g = empty_game((4, 4, King(Color.WHITE)))
        g.play(m(4, 4, 3, 3))
        g = empty_game((4, 4, King(Color.WHITE)))
        with self.assertRaises(InvalidMove):
            g.play(m(4, 4, 2, 4))


class TestSelectionUndoScenarios(unittest.TestCase):
    def test_selection_uses_same_validators(self):
        g = Game()
        g.validate_selection(Position(6, 4))
        with self.assertRaises(InvalidMove) as e:
            g.validate_selection(Position(1, 4))
        self.assertEqual(e.exception.code, "owned_by_current_player")
        with self.assertRaises(InvalidMove) as e:
            g.validate_selection(Position(4, 4))
        self.assertEqual(e.exception.code, "piece_exists")

    def test_error_code_is_validator_name(self):
        with self.assertRaises(InvalidMove) as e:
            Game().play(m(7, 0, 5, 0))
        self.assertEqual(e.exception.code, "follows_piece_rules")

    def test_legal_destinations(self):
        g = Game()
        self.assertEqual(sorted((p.row, p.col) for p in g.legal_destinations(Position(7, 1))), [(5, 0), (5, 2)])
        self.assertEqual(g.legal_destinations(Position(1, 1)), [])   # not White's piece

    def test_undo_restores_board_and_turn(self):
        g = empty_game((4, 4, Pawn(Color.WHITE)), (3, 5, Pawn(Color.BLACK)))
        g.play(m(4, 4, 3, 5))
        self.assertEqual(g.captured_by(Color.WHITE)[0].name, "Pawn")
        self.assertTrue(g.undo())
        self.assertIs(g.turn, Color.WHITE)
        self.assertIsInstance(g.board.get(Position(3, 5)), Pawn)
        self.assertFalse(g.undo())

    def test_scenarios_load(self):
        from scenarios import SCENARIOS, board_for
        for key in SCENARIOS:
            board_for(key)
        g = Game(board_for("knight"))
        self.assertEqual(len(g.legal_destinations(Position(4, 4))), 8)   # boxed-in knight still jumps


if __name__ == "__main__":
    unittest.main()
