import math
import time
import tkinter as tk
import numpy as np
from random import random
from lib.tetromins.imports import tetromin_list
from lib.base_types import TetrominGrid

GRID_WIDTH = 10
GRID_HEIGHT_INVISIBLE = 2
GRID_HEIGHT = 20 + GRID_HEIGHT_INVISIBLE
SQUARE_SIZE_PX = 30
CANVAS_BORDER_WIDTH = 10
CANVAS_WIDTH = GRID_WIDTH * SQUARE_SIZE_PX + CANVAS_BORDER_WIDTH
CANVAS_HEIGHT = (GRID_HEIGHT - GRID_HEIGHT_INVISIBLE) * \
    SQUARE_SIZE_PX + CANVAS_BORDER_WIDTH


tk_root = tk.Tk()
tk_root.title('PyTetris')

level_label_text = tk.StringVar()
level_label = tk.Label(tk_root, textvariable=level_label_text)
level_label.grid(row=0, column=0, sticky="w", padx=CANVAS_BORDER_WIDTH//2)

gameover_label_text = tk.StringVar()
gameover_label = tk.Label(tk_root, textvariable=gameover_label_text)
gameover_label.grid(row=0, column=1, sticky="we")

score_label_text = tk.StringVar()
score_label = tk.Label(tk_root, textvariable=score_label_text)
score_label.grid(row=0, column=2, sticky="e", padx=CANVAS_BORDER_WIDTH//2)

canvas = tk.Canvas(tk_root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT)
canvas.grid(row=1, column=0, columnspan=3)


def ms_now():
    return int(time.time()*1000)


def disable_on_gameover(f):
    def wrapper(*args):
        self_tsm = args[0]
        if self_tsm.game_is_over:
            raise Exception(
                'Game is over, you cannot pass controls to it anymore.')
        return f(*args)
    return wrapper


class TetrisStateMachine:
    def __init__(self):
        self.width = GRID_WIDTH
        self.height = GRID_HEIGHT
        self.reset()

    def reset(self):
        self.grid = [[None for j in range(self.width)]
                     for i in range(self.height)]
        self.last_game_tick_ms = 0
        self.game_score = 0
        self.game_lines_cleared = 0
        self.game_level = 0
        self.game_is_over = False
        self.current_tetromin = None
        self.set_next_tetromin()
        self.start()

    def start(self):
        self.last_game_tick_ms = ms_now()

    def get_current_game_tick_ms_T(self):
        game_speed_seconds = (0.8-self.game_level*0.007)**self.game_level
        return int(max(0, game_speed_seconds)*1000)

    def should_game_tick(self):
        now = ms_now()
        return now - self.last_game_tick_ms >= self.get_current_game_tick_ms_T()

    def skip_game_tick(self):
        self.last_game_tick_ms = ms_now()

    def next_game_tick(self):
        if self.game_is_over:
            return

        self.last_game_tick_ms = ms_now()
        self.tetromin_down()

    def set_next_tetromin(self):
        tetro = tetromin_list[int(random()*len(tetromin_list))]()

        self.current_tetromin = {
            'tetro': tetro,
            'x': self.width//2 - 1,
            'y': 1
        }

        # checks if current tetromin that was placed is in red zone or "end game"
        if self.current_tetromin and self.does_current_tetromin_collide() and self.is_current_tetromin_in_spawn_area():
            self.game_is_over = True
            return

        self.skip_game_tick()

    def unpack_current_tetromin(self):
        tetro = self.current_tetromin['tetro']
        tx = self.current_tetromin['x']
        ty = self.current_tetromin['y']
        return tetro, tx, ty

    def is_current_tetromin_in_spawn_area(self) -> bool:
        tetro, tx, ty = self.unpack_current_tetromin()
        tetro_grid = tetro.current_grid()

        for y in range(tetro.height()):
            for x in range(tetro.width()):
                gx = tx + x
                gy = ty + y
                if tetro_grid[y][x] and ty < GRID_HEIGHT_INVISIBLE:
                    return True

        return False

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
        lines_combo = 0
        while y >= 0:
            if self.is_row_full(y):
                self.remove_row(y)
                lines_combo += 1
            else:
                y -= 1
                if lines_combo > 0:
                    self.apply_lines_cleared(lines_combo)
                    lines_combo = 0

    def apply_lines_cleared(self, lines_cleared: int):
        self.game_score += self.calculate_break_rows_score(lines_cleared)
        self.game_lines_cleared += lines_cleared
        self.game_level = self.game_lines_cleared // 10

    def calculate_break_rows_score(self, lines_combo: int) -> int:
        max_lines_combo = 4
        lines_multiplier = [0, 40, 100, 300, 1200]  # 1 2 3 and 4
        lines_combo = min(lines_combo, max_lines_combo)
        return lines_multiplier[lines_combo] * (self.game_level + 1)

    def burn_current_tetromin_into_grid(self):
        tetro, tx, ty = self.unpack_current_tetromin()
        tetro_grid = tetro.current_grid()
        for y in range(tetro.height()):
            for x in range(tetro.width()):
                if tetro_grid[y][x]:
                    self.grid[ty+y][tx+x] = tetro.color

        self.break_full_rows()

    @disable_on_gameover
    def tetromin_down(self, process_logic_on_collision=True):
        self.skip_game_tick()
        self.current_tetromin['y'] += 1
        if collides := self.does_current_tetromin_collide():
            self.current_tetromin['y'] -= 1
            if process_logic_on_collision:
                self.burn_current_tetromin_into_grid()
                self.set_next_tetromin()
        return collides

    @disable_on_gameover
    def tetromin_left(self):
        self.current_tetromin['x'] -= 1
        if collides := self.does_current_tetromin_collide():
            self.current_tetromin['x'] += 1
        return collides

    @disable_on_gameover
    def tetromin_right(self):
        self.current_tetromin['x'] += 1
        if collides := self.does_current_tetromin_collide():
            self.current_tetromin['x'] -= 1
        return collides

    @disable_on_gameover
    def tetromin_rotate(self):
        self.current_tetromin['tetro'].rotate()
        if collides := self.does_current_tetromin_collide():
            self.current_tetromin['tetro'].rotate(backward=True)
        return collides

    @disable_on_gameover
    def tetromin_harddrop(self):
        hard_drop_points = 0
        while not self.tetromin_down():
            hard_drop_points += 1
        self.game_score += hard_drop_points

    def get_render_grid(self):
        render_grid = [[self.grid[i][j] for j in range(self.width)]
                       for i in range(self.height)]
        current_tetro = self.current_tetromin

        tetro, tx, ty = self.unpack_current_tetromin()
        tetro_grid = tetro.current_grid()

        # dont show its position if game is over. Only show the "burned in" tetromins.
        if not self.game_is_over:
            for y in range(tetro.height()):
                for x in range(tetro.width()):
                    gx = tx+x
                    gy = ty+y
                    if tetro_grid[y][x] and gx >= 0 and gy >= 0 and gx < self.width and gy < self.height:
                        render_grid[gy][gx] = tetro.color

        return render_grid


TSM = TetrisStateMachine()


def key_press(event):
    print("key pressed", event, repr(event.keysym))
    if event.keysym == 'Up':
        TSM.tetromin_rotate()

    elif event.keysym == 'Left':
        TSM.tetromin_left()

    elif event.keysym == 'Right':
        TSM.tetromin_right()

    elif event.keysym == 'Down':
        TSM.tetromin_down()

    elif event.keysym == 'space':
        TSM.tetromin_harddrop()

    elif event.keysym.lower() == 'r':
        TSM.reset()

    render(canvas, TSM.get_render_grid())


def on_aiplay():
    # this is not working. its just a pseudo code of 'intepretation'
    command_sequence = TSM.ai_commands()
    for command in command_sequence:
        key_press(command)
        render()
        sleep(16)


def on_gameloop():
    if TSM.should_game_tick():
        TSM.next_game_tick()
    render(canvas, TSM.get_render_grid())
    level_label_text.set(f'Level: {TSM.game_level+1}')
    score_label_text.set(f'Score: {TSM.game_score}')
    gameover_label_text.set(
        f'{"GAME OVER! (R = Restart)" if TSM.game_is_over else ""}')
    tk_root.after(16, on_gameloop)


def render_rect(canvas, x, y, dim, fill):
    x += CANVAS_BORDER_WIDTH // 2 + 1
    y += CANVAS_BORDER_WIDTH // 2 + 1
    canvas.create_rectangle(x, y, x+dim, y+dim, fill=fill)


def clear_canvas(canvas):
    canvas.delete(tk.ALL)


def render(canvas, grid):
    clear_canvas(canvas)
    for y_idx in range(GRID_HEIGHT_INVISIBLE, GRID_HEIGHT):
        for x_idx in range(GRID_WIDTH):
            item = grid[y_idx][x_idx]
            render_rect(canvas, x_idx * SQUARE_SIZE_PX, (y_idx-GRID_HEIGHT_INVISIBLE) *
                        SQUARE_SIZE_PX, SQUARE_SIZE_PX, item or 'white')
# TODO:
# * Code refactoring.
# * Next piece on the line
# * AI!

def start():
    tk_root.bind("<Key>", key_press)
    TSM.start()
    on_gameloop()
    tk.mainloop()


start()
