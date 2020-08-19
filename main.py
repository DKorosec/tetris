import math
import tkinter as tk
import numpy as np
from random import random
from lib.tetromins.imports import tetromin_list
from lib.base_types import TetrominGrid

GRID_WIDTH = 10
GRID_HEIGHT = 20
SQUARE_SIZE_PX = 30
CANVAS_WIDTH = GRID_WIDTH * SQUARE_SIZE_PX
CANVAS_HEIGHT = GRID_HEIGHT * SQUARE_SIZE_PX


tk_root = tk.Tk()
tk_root.title('PyTetris')
canvas = tk.Canvas(tk_root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT)
canvas.pack()


class TetrisStateMachine:
    def __init__(self):
        self.width = GRID_WIDTH
        self.height = GRID_HEIGHT
        self.grid = [[None for j in range(self.width)]
                     for i in range(self.height)]
        self.set_next_tetromin()

    def set_next_tetromin(self):
        tetro = tetromin_list[int(random()*len(tetromin_list))]()
        # TODO: requires work with spawning in the "invisible zone"
        # getting the real bottom of tetromin, because some squares are 0.
        self.current_tetromin = {
            'tetro': tetro,
            'x': self.width//2,
            'y': 0
        }

    def unpack_current_tetromin(self):
        tetro = self.current_tetromin['tetro']
        tx = self.current_tetromin['x']
        ty = self.current_tetromin['y']
        return tetro, tx, ty

    def does_current_tetromin_collide(self) -> bool:
        tetro, tx, ty = self.unpack_current_tetromin()
        tetro_grid = tetro.current_grid()

        for y in range(tetro.height()):
            for x in range(tetro.width()):
                gx = tx + x
                gy = ty + y
                if not tetro_grid[y][x]:
                    continue

                out_of_bounds = gx < 0 or gx >= self.width or gy < 0 or gy >= self.height

                if out_of_bounds or self.grid[gy][gx]:
                    return True

        return False

    def is_row_full(self, row: int) -> bool:
        for x in range(self.width):
            if not self.grid[row][x]:
                return False
        return True

    def remove_row(self, row: int):
        while row >= 0:
            for x in range(self.width):
                self.grid[row][x] = None
                if row-1 >= 0:
                    self.grid[row][x] = self.grid[row-1][x]
            row -= 1

    def break_full_rows(self):
        y = self.height - 1
        # go up the rows!
        while y >= 0:
            if self.is_row_full(y):
                self.remove_row(y)
            else:
                y -= 1

    def burn_current_tetromin_into_grid(self):
        # TODO: this will crash when figure has collision at the top of the grid
        # the collision check ignores the y < 0 checks and burning into the grid will go out of bounds
        tetro, tx, ty = self.unpack_current_tetromin()
        tetro_grid = tetro.current_grid()
        for y in range(tetro.height()):
            for x in range(tetro.width()):
                if tetro_grid[y][x]:
                    self.grid[ty+y][tx+x] = tetro.color

        self.break_full_rows()

    def tetromin_down(self, process_logic_on_collision=True):
        self.current_tetromin['y'] += 1
        if collides := self.does_current_tetromin_collide():
            self.current_tetromin['y'] -= 1
            if process_logic_on_collision:
                self.burn_current_tetromin_into_grid()
                self.set_next_tetromin()
        return collides

    def tetromin_left(self):
        self.current_tetromin['x'] -= 1
        if collides := self.does_current_tetromin_collide():
            self.current_tetromin['x'] += 1
        return collides

    def tetromin_right(self):
        self.current_tetromin['x'] += 1
        if collides := self.does_current_tetromin_collide():
            self.current_tetromin['x'] -= 1
        return collides

    def tetromin_rotate(self):
        self.current_tetromin['tetro'].rotate()
        if collides := self.does_current_tetromin_collide():
            self.current_tetromin['tetro'].rotate(backward=True)
        return collides

    def tetromin_falldown(self):
        while not self.tetromin_down():
            pass

    def get_render_grid(self):
        render_grid = [[self.grid[i][j] for j in range(self.width)]
                       for i in range(self.height)]
        current_tetro = self.current_tetromin

        tetro, tx, ty = self.unpack_current_tetromin()
        tetro_grid = tetro.current_grid()

        for y in range(tetro.height()):
            for x in range(tetro.width()):
                gx = tx+x
                gy = ty+y
                if tetro_grid[y][x] and gx >= 0 and gy >= 0 and gx < self.width and gy < self.height:
                    render_grid[gy][gx] = tetro.color

        return render_grid


TSM = TetrisStateMachine()


def key_press(event):
    print("pressed", event, repr(event.keysym), event.keysym == 'Left')
    if event.keysym == 'Up':
        TSM.tetromin_rotate()
    if event.keysym == 'Left':
        TSM.tetromin_left()
    if event.keysym == 'Right':
        TSM.tetromin_right()
    if event.keysym == 'Down':
        TSM.tetromin_down()
    if event.keysym == 'space':
        TSM.tetromin_falldown()

    on_gameloop(False)
    # TODO: state machine .key_left(), key_right(), ...


def on_gameloop(auto_loop=True):
    # TODO: Remove auto_loop=True.
    # do deltaTime and render if enough time was passed. This way we can correctly implement fast down shift of tetromins.

    x = int(random() * GRID_WIDTH)
    y = int(random() * GRID_HEIGHT)
    grid = TSM.get_render_grid()
    if auto_loop:
        # TSM.tetro_down() -> logic checks if col and spawns next.
        TSM.tetromin_down()
        tk_root.after(500, on_gameloop)
    render(canvas, grid)


def render_rect(canvas, x, y, dim, fill):
    canvas.create_rectangle(x, y, x+dim, y+dim, fill=fill)


def clear_canvas(canvas):
    canvas.delete(tk.ALL)


def render(canvas, grid):
    clear_canvas(canvas)
    for y_idx in range(GRID_HEIGHT):
        for x_idx in range(GRID_WIDTH):
            item = grid[y_idx][x_idx]
            render_rect(canvas, x_idx * SQUARE_SIZE_PX, y_idx *
                        SQUARE_SIZE_PX, SQUARE_SIZE_PX, item or 'white')


def start():
    tk_root.bind("<Key>", key_press)
    on_gameloop()
    tk.mainloop()


start()
