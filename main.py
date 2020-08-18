import math
import tkinter as tk
import numpy as np
from random import random
from lib.tetromins.imports import tetromin_list

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
        self.current_tetromin = {
            'tetro': tetro,
            'x': self.width//2,
            'y': 0
        }

    def get_render_grid(self):
        render_grid = [[self.grid[i][j] for j in range(self.width)]
                       for i in range(self.height)]
        current_tetro = self.current_tetromin
        tetro = current_tetro['tetro']
        tx = current_tetro['x']
        ty = current_tetro['y']
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
        # TSM.tetro_rotate()
        TSM.current_tetromin['tetro'].rotate()
    if event.keysym == 'Left':
        # TSM.tetro_left()
        TSM.current_tetromin['x'] -= 1
    if event.keysym == 'Right':
        # TSM.tetro_right()
        TSM.current_tetromin['x'] += 1
    if event.keysym == 'Down':
        # TSM.tetro_down()
        TSM.current_tetromin['y'] += 1
    if event.keysym == 'space':
        # TSM.tetro_fall_down()
        TSM.set_next_tetromin()
    on_gameloop(False)
    # TODO: state machine .key_left(), key_right(), ...


def on_gameloop(auto_loop=True):
    x = int(random() * GRID_WIDTH)
    y = int(random() * GRID_HEIGHT)
    grid = TSM.get_render_grid()
    if auto_loop:
        # TSM.tetro_down() -> logic checks if col and spawns next.
        TSM.current_tetromin['y'] += 1
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
