from time import sleep
import tkinter as tk
from random import random
from lib.ai_tetris_state_machine import AiTetrisStateMachine
from lib.tetris_state_machine import GRID_HEIGHT, GRID_WIDTH, GRID_HEIGHT_INVISIBLE

TSM = AiTetrisStateMachine()
TOGGLE_FULLSCREEN = False
TOGGLE_AUTOPILOT = False
COMMAND_QUEUE = []

SQUARE_SIZE_PX = 30
CANVAS_BORDER_WIDTH = 10
CANVAS_WIDTH = GRID_WIDTH * SQUARE_SIZE_PX + CANVAS_BORDER_WIDTH
CANVAS_HEIGHT = (GRID_HEIGHT - GRID_HEIGHT_INVISIBLE) * \
    SQUARE_SIZE_PX + CANVAS_BORDER_WIDTH

GRID_NEXT_TETROMIN_WIDTH = 4
GRID_NEXT_TETROMIN_HEIGHT = 2
CANVAS_NEXT_TETROMIN_WIDTH = SQUARE_SIZE_PX * \
    GRID_NEXT_TETROMIN_WIDTH + CANVAS_BORDER_WIDTH
CANVAS_NEXT_TETROMIN_HEIGHT = SQUARE_SIZE_PX * \
    GRID_NEXT_TETROMIN_HEIGHT + CANVAS_BORDER_WIDTH


tk_root = tk.Tk()
tk_root.iconphoto(False, tk.PhotoImage(file='icon.png'))
tk_root.resizable(False, False)
tk_root.title('PyTetris')


tk_root.grid_rowconfigure(3, weight=1)
# labels

level_label_text = tk.StringVar()
level_label = tk.Label(tk_root, textvariable=level_label_text)
level_label.grid(row=0, column=1, sticky="nw", pady=CANVAS_BORDER_WIDTH//2)

score_label_text = tk.StringVar()
score_label = tk.Label(tk_root, textvariable=score_label_text)
score_label.grid(row=1, column=1, sticky="nw")

gameover_label_text = tk.StringVar()
gameover_label = tk.Label(tk_root, textvariable=gameover_label_text)
gameover_label.grid(row=3, column=1, sticky="new")

# render canvases
canvas = tk.Canvas(tk_root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT)
canvas.grid(row=0, column=0, rowspan=4, sticky="NESW")

next_tetromin_canvas = tk.Canvas(
    tk_root, width=CANVAS_NEXT_TETROMIN_WIDTH, height=CANVAS_NEXT_TETROMIN_HEIGHT, highlightbackground='black', highlightthickness=1)
next_tetromin_canvas.grid(
    row=2, column=1, pady=CANVAS_BORDER_WIDTH*2, padx=CANVAS_BORDER_WIDTH, sticky="NESW")


def render(canvas):
    def render_rect(canvas, x, y, dim, fill):
        x += CANVAS_BORDER_WIDTH // 2 + 1
        y += CANVAS_BORDER_WIDTH // 2 + 1
        canvas.create_rectangle(x, y, x+dim, y+dim, fill=fill, outline='black')

    grid = TSM.get_render_grid()
    canvas.delete(tk.ALL)
    next_tetromin_canvas.delete(tk.ALL)
    for y_idx in range(GRID_HEIGHT_INVISIBLE, GRID_HEIGHT):
        for x_idx in range(GRID_WIDTH):
            item = grid[y_idx][x_idx]
            render_rect(canvas, x_idx * SQUARE_SIZE_PX, (y_idx-GRID_HEIGHT_INVISIBLE) *
                        SQUARE_SIZE_PX, SQUARE_SIZE_PX, item or 'grey')

    next_tetro = TSM.next_tetromin
    next_tetro_grid = next_tetro.current_grid()

    # we know that tetro with 0 rotations (default state) is always defined in first two rows!
    render_offset = CANVAS_NEXT_TETROMIN_WIDTH/2 - \
        (next_tetro.width()*SQUARE_SIZE_PX / 2) - CANVAS_BORDER_WIDTH / 2
    for y in range(2):
        for x in range(next_tetro.width()):
            if next_tetro_grid[y][x]:
                render_rect(next_tetromin_canvas, render_offset + x * SQUARE_SIZE_PX,
                            y*SQUARE_SIZE_PX, SQUARE_SIZE_PX, next_tetro.color)

    next_level_p = int((TSM.game_lines_cleared % 10)/10 * 100)
    level_label_text.set(f'Level: {TSM.get_game_level()+1} ({next_level_p}%)')
    score_label_text.set(f'Score: {TSM.game_score}')

    nl = '\n\r'
    muted_mode_txt = 'ON' if TSM.is_muted() else 'OFF'
    fullscreen_mode_txt = 'ON' if TOGGLE_FULLSCREEN else 'OFF'
    autopilot_mode_txt = 'ON' if TOGGLE_AUTOPILOT else 'OFF'
    controls_text = f'Controls:{nl}Arrow keys = Move figure{nl}Space = Hard drop{nl}R = Reset{nl}----{nl}F11=toggle fullscreen [{fullscreen_mode_txt}]{nl}M=toggle mute [{muted_mode_txt}]{nl}A=toggle autopilot [{autopilot_mode_txt}]{nl}1-9=restart at level'
    gameover_label_text.set(
        f'{f"GAME OVER!{nl}Press R to reset" if TSM.game_is_over else f"{controls_text}"}')


KONAMI_CODE = ['up', 'up', 'down', 'down',
               'left', 'right', 'left', 'right', 'b', 'a']
KONAMI_CODE_I = 0


def handle_konami_code(string: str):
    global KONAMI_CODE_I

    if KONAMI_CODE_I == len(KONAMI_CODE):
        tk_root.title('Huti Tuti')

    elif string == KONAMI_CODE[KONAMI_CODE_I]:
        KONAMI_CODE_I += 1
        handle_konami_code('')
    elif string != '':
        KONAMI_CODE_I = 0


def unset_ai_commands():
    global COMMAND_QUEUE
    global TOGGLE_AUTOPILOT
    TOGGLE_AUTOPILOT = False
    COMMAND_QUEUE = []

def key_press(event):
    global TOGGLE_FULLSCREEN
    global COMMAND_QUEUE
    global TOGGLE_AUTOPILOT

    handle_konami_code(event.keysym.lower())

    if event.keysym == 'Up':
        unset_ai_commands()
        TSM.tetromin_rotate()

    elif event.keysym == 'Left':
        unset_ai_commands()
        TSM.tetromin_left()

    elif event.keysym == 'Right':
        unset_ai_commands()
        TSM.tetromin_right()

    elif event.keysym == 'Down':
        unset_ai_commands()
        TSM.tetromin_down()

    elif event.keysym == 'space':
        unset_ai_commands()
        TSM.tetromin_harddrop()

    elif event.keysym.lower() == 'r':
        TSM.reset()

    elif event.keysym.lower() == 'm':
        TSM.unmute() if TSM.is_muted() else TSM.mute()

    elif event.keysym == 'F11':
        TOGGLE_FULLSCREEN = not TOGGLE_FULLSCREEN
        tk_root.attributes('-fullscreen', TOGGLE_FULLSCREEN)

    elif event.keysym.lower() == 'a':
        TOGGLE_AUTOPILOT = not TOGGLE_AUTOPILOT
        COMMAND_QUEUE = []

    elif event.keysym.isnumeric():
        level_value = int(event.keysym)
        if level_value > 0:
            TSM.set_level(level_value-1)

    render(canvas)


def on_gameloop():
    global COMMAND_QUEUE
    if TOGGLE_AUTOPILOT:
        if not len(COMMAND_QUEUE):
            COMMAND_QUEUE = TSM.generate_best_fit_path_commands() or [lambda: None]

        cmd = COMMAND_QUEUE.pop(0) 
        cmd()
    elif TSM.should_game_tick(): 
        TSM.next_game_tick()

    render(canvas)
    tk_root.after(1 if TOGGLE_AUTOPILOT else 16, on_gameloop)
    handle_window_resizing()


def handle_window_resizing():
    global SQUARE_SIZE_PX
    global CANVAS_NEXT_TETROMIN_WIDTH
    global CANVAS_NEXT_TETROMIN_HEIGHT
    global CANVAS_WIDTH
    global CANVAS_HEIGHT

    SQUARE_SIZE_PX = (tk_root.winfo_height() - CANVAS_BORDER_WIDTH //
                      2) // (GRID_HEIGHT - GRID_HEIGHT_INVISIBLE)

    CANVAS_NEXT_TETROMIN_WIDTH = SQUARE_SIZE_PX * \
        GRID_NEXT_TETROMIN_WIDTH + CANVAS_BORDER_WIDTH

    CANVAS_NEXT_TETROMIN_HEIGHT = SQUARE_SIZE_PX * \
        GRID_NEXT_TETROMIN_HEIGHT + CANVAS_BORDER_WIDTH

    CANVAS_WIDTH = (GRID_WIDTH+0.25) * SQUARE_SIZE_PX
    CANVAS_HEIGHT = tk_root.winfo_height() + CANVAS_BORDER_WIDTH

    canvas.configure(height=CANVAS_HEIGHT, width=CANVAS_WIDTH)

    next_tetromin_canvas.configure(
        height=CANVAS_NEXT_TETROMIN_HEIGHT, width=CANVAS_NEXT_TETROMIN_WIDTH)

    canvas.grid_configure(padx=(tk_root.winfo_width()//2 - canvas.winfo_width()//2, 0)
                          if TOGGLE_FULLSCREEN else (0, 0))


def center(win):
    win.update_idletasks()
    width = win.winfo_width()
    height = win.winfo_height()
    x = (win.winfo_screenwidth() // 2) - (width // 2)
    y = (win.winfo_screenheight() // 2) - (height // 2)
    win.geometry('{}x{}+{}+{}'.format(width, height, x, y))


def start():
    tk_root.bind("<Key>", key_press)
    center(tk_root)
    TSM.reset()
    on_gameloop()
    tk.mainloop()


start()

# TODO:
# ML ai - meta learning the best heuristics? Somewhere in the future if i have time ;)