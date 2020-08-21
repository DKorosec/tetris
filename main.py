import tkinter as tk
from random import random
from lib.tetris_state_machine import TetrisStateMachine, GRID_HEIGHT, GRID_WIDTH, GRID_HEIGHT_INVISIBLE

TSM = TetrisStateMachine()
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


def render(canvas, grid):
    def render_rect(canvas, x, y, dim, fill):
        x += CANVAS_BORDER_WIDTH // 2 + 1
        y += CANVAS_BORDER_WIDTH // 2 + 1
        canvas.create_rectangle(x, y, x+dim, y+dim, fill=fill, outline='black')

    canvas.delete(tk.ALL)
    for y_idx in range(GRID_HEIGHT_INVISIBLE, GRID_HEIGHT):
        for x_idx in range(GRID_WIDTH):
            item = grid[y_idx][x_idx]
            render_rect(canvas, x_idx * SQUARE_SIZE_PX, (y_idx-GRID_HEIGHT_INVISIBLE) *
                        SQUARE_SIZE_PX, SQUARE_SIZE_PX, item or 'gray')

    level_label_text.set(f'Level: {TSM.game_level+1}')
    score_label_text.set(f'Score: {TSM.game_score}')
    gameover_label_text.set(
        f'{"GAME OVER! (R = Restart)" if TSM.game_is_over else "(R = Restart)"}')


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


def on_gameloop():
    if TSM.should_game_tick():
        TSM.next_game_tick()
    render(canvas, TSM.get_render_grid())
    tk_root.after(16, on_gameloop)


def start():
    tk_root.bind("<Key>", key_press)
    TSM.start()
    on_gameloop()
    tk.mainloop()


start()

# TODO:
# * Next piece on the line (UI and functionality - watch todo in on reset())
# * AI!
# def on_aiplay():
#     # this is not working. its just a pseudo code of 'intepretation'
#     command_sequence = TSM.ai_commands()
#     for command in command_sequence:
#         key_press(command)
#         render()
#         sleep(16)
