"""
Snake game logic — pure Python, no GUI. Fully unit-testable.

Grid coordinates: (x, y) = (column, row), origin top-left.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

Cell = tuple[int, int]

COLS, ROWS = 35, 20


class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    @property
    def opposite(self) -> "Direction":
        dx, dy = self.value
        return Direction((-dx, -dy))


@dataclass(frozen=True)
class Rect:
    """Obstacle in grid cells, inclusive bounds."""
    x1: int
    y1: int
    x2: int
    y2: int

    def contains(self, cell: Cell) -> bool:
        x, y = cell
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2

    def cells(self) -> set[Cell]:
        return {(x, y) for x in range(self.x1, self.x2 + 1)
                for y in range(self.y1, self.y2 + 1)}


# The four "windows" from the original version, now defined once.
DEFAULT_OBSTACLES = (
    Rect(1, 8, 3, 17),
    Rect(14, 8, 16, 17),
    Rect(18, 8, 20, 17),
    Rect(31, 8, 33, 17),
)


@dataclass
class Snake:
    name: str
    body: list[Cell]                      # body[0] is the head
    direction: Direction = Direction.RIGHT
    alive: bool = True
    score: int = 0
    _next_direction: Optional[Direction] = field(default=None, repr=False)

    @classmethod
    def spawn(cls, name: str, head: Cell, length: int = 5,
              direction: Direction = Direction.RIGHT) -> "Snake":
        dx, dy = direction.value
        body = [(head[0] - i * dx, head[1] - i * dy) for i in range(length)]
        return cls(name, body, direction)

    @property
    def head(self) -> Cell:
        return self.body[0]

    def turn(self, direction: Direction) -> None:
        # Compare against the direction actually executed last tick, not the
        # last key pressed -> two quick key presses can't reverse the snake.
        if direction is not self.direction.opposite:
            self._next_direction = direction

    def next_head(self) -> Cell:
        if self._next_direction:
            self.direction = self._next_direction
            self._next_direction = None
        dx, dy = self.direction.value
        return self.head[0] + dx, self.head[1] + dy


class Game:
    POINTS_PER_FOOD = 10

    def __init__(self, cols: int = COLS, rows: int = ROWS,
                 obstacles: tuple[Rect, ...] = DEFAULT_OBSTACLES,
                 snakes: Optional[list[Snake]] = None,
                 rng: Optional[random.Random] = None):
        self.cols, self.rows = cols, rows
        self.obstacles = obstacles
        self.rng = rng or random.Random()
        self.snakes = snakes if snakes is not None else [
            Snake.spawn("Türkis", head=(4, 1)),
            Snake.spawn("Orange", head=(4, 3)),
        ]
        self.food: Optional[Cell] = None
        self.place_food()

    # ---------------------------------------------------------------- queries
    def in_bounds(self, cell: Cell) -> bool:
        x, y = cell
        return 0 <= x < self.cols and 0 <= y < self.rows

    def is_obstacle(self, cell: Cell) -> bool:
        return any(r.contains(cell) for r in self.obstacles)

    @property
    def is_over(self) -> bool:
        return not any(s.alive for s in self.snakes)

    def winner(self) -> Optional[Snake]:
        """Highest score; None on a tie."""
        ranked = sorted(self.snakes, key=lambda s: s.score, reverse=True)
        if len(ranked) > 1 and ranked[0].score == ranked[1].score:
            return None
        return ranked[0]

    # --------------------------------------------------------------- commands
    def place_food(self) -> None:
        occupied = {c for s in self.snakes for c in s.body}
        free = [(x, y) for x in range(self.cols) for y in range(self.rows)
                if (x, y) not in occupied and not self.is_obstacle((x, y))]
        self.food = self.rng.choice(free) if free else None

    def tick(self) -> None:
        """Advance one step. All alive snakes move simultaneously."""
        alive = [s for s in self.snakes if s.alive]
        new_heads = {id(s): s.next_head() for s in alive}

        # Body each snake will have after this tick (if it survives).
        future: dict[int, list[Cell]] = {}
        for s in self.snakes:
            if not s.alive:
                future[id(s)] = s.body            # dead snakes stay as obstacles
                continue
            head = new_heads[id(s)]
            grows = head == self.food
            future[id(s)] = [head] + (s.body if grows else s.body[:-1])

        # Decide deaths using the future positions of everyone.
        dying = []
        for s in alive:
            head = new_heads[id(s)]
            hit = (not self.in_bounds(head)
                   or self.is_obstacle(head)
                   or head in future[id(s)][1:])
            for other in self.snakes:
                if other is not s and head in future[id(other)]:
                    hit = True                     # includes head-on collisions
            if hit:
                dying.append(s)

        ate = False
        for s in alive:
            if s in dying:
                s.alive = False                    # dead snake doesn't move or eat
                continue
            s.body = future[id(s)]
            if s.head == self.food:
                s.score += self.POINTS_PER_FOOD
                ate = True
        if ate:
            self.place_food()
