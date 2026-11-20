import random
import unittest

from snake_model import Direction, Game, Rect, Snake


def game(*snakes, food=None, obstacles=(), cols=10, rows=10):
    g = Game(cols, rows, obstacles=obstacles, snakes=list(snakes), rng=random.Random(0))
    g.food = food
    return g


class TestMovement(unittest.TestCase):
    def test_moves_forward(self):
        s = Snake.spawn("a", (3, 0), length=3)
        game(s).tick()
        self.assertEqual(s.body, [(4, 0), (3, 0), (2, 0)])

    def test_cannot_reverse_with_two_quick_keys(self):
        s = Snake.spawn("a", (3, 5), length=3)       # moving RIGHT
        g = game(s)
        s.turn(Direction.UP)
        s.turn(Direction.LEFT)                      # opposite of executed dir -> ignored
        g.tick()
        self.assertTrue(s.alive)
        self.assertEqual(s.head, (3, 4))

    def test_tail_cell_is_free_to_enter(self):
        # Head chasing its own tail in a 2x2 loop must not die.
        s = Snake("a", [(0, 0), (0, 1), (1, 1), (1, 0)], Direction.UP)
        g = game(s)
        s.turn(Direction.RIGHT)
        g.tick()
        self.assertTrue(s.alive)


class TestCollisions(unittest.TestCase):
    def test_wall(self):
        s = Snake.spawn("a", (9, 0), length=2)
        g = game(s)
        g.tick()
        self.assertFalse(s.alive)
        self.assertTrue(g.is_over)

    def test_obstacle(self):
        s = Snake.spawn("a", (2, 0), length=2)
        game(s, obstacles=(Rect(3, 0, 3, 0),)).tick()
        self.assertFalse(s.alive)

    def test_self(self):
        s = Snake("a", [(2, 2), (2, 3), (3, 3), (3, 2), (3, 1)], Direction.UP)
        g = game(s)
        s.turn(Direction.RIGHT)
        g.tick()
        self.assertFalse(s.alive)

    def test_other_body(self):
        a = Snake.spawn("a", (2, 0), length=2, direction=Direction.DOWN)
        b = Snake("b", [(5, 1), (4, 1), (3, 1), (2, 1), (1, 1)], Direction.RIGHT)
        g = game(a, b)
        g.tick()
        self.assertFalse(a.alive)
        self.assertTrue(b.alive)

    def test_head_on_kills_both(self):
        a = Snake.spawn("a", (3, 0), length=2, direction=Direction.RIGHT)
        b = Snake.spawn("b", (5, 0), length=2, direction=Direction.LEFT)
        g = game(a, b)
        g.tick()
        self.assertFalse(a.alive)
        self.assertFalse(b.alive)

    def test_dead_snake_cannot_eat(self):
        s = Snake.spawn("a", (9, 0), length=2)
        g = game(s, food=(9, 0))
        g.tick()
        self.assertEqual(s.score, 0)


class TestFood(unittest.TestCase):
    def test_eat_grows_and_scores(self):
        s = Snake.spawn("a", (3, 0), length=3)
        g = game(s, food=(4, 0))
        g.tick()
        self.assertEqual(len(s.body), 4)
        self.assertEqual(s.score, Game.POINTS_PER_FOOD)
        self.assertNotEqual(g.food, (4, 0))

    def test_food_never_on_snake_or_obstacle(self):
        s = Snake.spawn("a", (4, 0), length=5)
        obstacle = Rect(0, 1, 9, 9)
        g = game(s, obstacles=(obstacle,))
        for _ in range(50):
            g.place_food()
            self.assertNotIn(g.food, s.body)
            self.assertFalse(obstacle.contains(g.food))

    def test_winner_and_tie(self):
        a, b = Snake.spawn("a", (2, 0)), Snake.spawn("b", (2, 2))
        g = game(a, b)
        self.assertIsNone(g.winner())
        a.score = 10
        self.assertIs(g.winner(), a)


if __name__ == "__main__":
    unittest.main()
