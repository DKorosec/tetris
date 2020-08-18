from typing import List
from lib.base_types import TetrominGrid


class Tetromin:
    def __init__(self, grid_rotations: List[TetrominGrid], color: str):
        self.grid_rotations = grid_rotations
        self.rotation = 0
        self.color = color

    def width(self) -> int:
        return len(self.current_grid()[0])

    def height(self) -> int:
        return len(self.current_grid())

    def current_grid(self) -> TetrominGrid:
        return self.grid_rotations[self.rotation % len(self.grid_rotations)]

    def peek_next_grid(self, backward=False) -> TetrominGrid:
        self.rotate(backward)
        next_grid = self.current_grid()
        self.rotate(not backward)
        return next_grid

    def rotate(self, backward=False) -> None:
        self.rotation += 1 if not backward else -1

    def debug_print(self) -> None:
        for row in self.current_grid():
            print(row)
