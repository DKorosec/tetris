import time
from random import random
from aupyom import Sampler, Sound
from lib.tetromins.imports import tetromin_list
import pygame

GRID_WIDTH = 10
GRID_HEIGHT_INVISIBLE = 2
GRID_HEIGHT = 20 + GRID_HEIGHT_INVISIBLE

sampler = Sampler()
theme_bg_sound = Sound.from_file("sounds/sound_track.wav")
theme_bg_sound.loop = True
theme_bg_sound.volume = 0.5

pygame.mixer.pre_init(44100, -16, 1, 512)
pygame.mixer.init()
pygame_loaded_sounds = []


def unmute_pygame_sounds():
    # required "hack/workaround" to call this fn else the library of aupyom bugs out.
    theme_bg_sound._zero_padding()
    theme_bg_sound.volume = 0.5
    for sound in pygame_loaded_sounds:
        sound['unmute']()


def mute_pygame_sounds():
    theme_bg_sound.volume = 0
    for sound in pygame_loaded_sounds:
        sound['mute']()


def load_pygame_sound(filename, default_volume=1.0):
    sound = pygame.mixer.Sound(filename)
    sound.set_volume(default_volume)
    pygame_loaded_sounds.append({
        'sound': sound,
        'unmute': lambda: sound.set_volume(default_volume),
        'mute': lambda: sound.set_volume(0.0)
    })
    return sound


sound_start = load_pygame_sound("sounds/se_game_start.wav", 0.25)
sound_harddrop = load_pygame_sound("sounds/se_game_landing.wav")
sound_move = load_pygame_sound("sounds/se_game_move_2.wav", 0.5)
sound_rotate = load_pygame_sound("sounds/se_game_rotate.wav", 0.25)
sound_lvlup = load_pygame_sound("sounds/se_game_lvlup.wav")
sound_invalid = load_pygame_sound("sounds/se_sys_alert.wav")
sound_gameover = load_pygame_sound("sounds/se_game_gameover.wav")

sound_combo1 = load_pygame_sound("sounds/se_game_single.wav")
sound_combo2 = load_pygame_sound("sounds/se_game_double.wav")
sound_combo3 = load_pygame_sound("sounds/se_game_triple.wav")
sound_combo4 = load_pygame_sound("sounds/se_game_tetris.wav")


def ms_now():
    return int(time.time()*1000)


def disable_on_gameover(f):
    def wrapper(*args, **kwargs):
        self_tsm = args[0]
        if self_tsm.game_is_over:
            sound_invalid.play()
            raise Exception(
                'Game is over, you cannot pass controls to it anymore.')
        return f(*args, **kwargs)
    return wrapper


class TetrisStateMachine:
    def __init__(self):
        self.width = GRID_WIDTH
        self.height = GRID_HEIGHT
        self._game_level: int = None
        self._muted = False
        self.reset(start=False)

    def _set_game_level(self, game_level: int):
        if self._game_level != game_level:
            self._game_level = game_level
            if game_level > 0:
                sound_lvlup.play()
            # handle music speed
            level_speed = [0.87, 0.95, 1.01, 1.15, 1.27, 1.4,
                           1.5, 1.66, 1.77, 1.88, 1.99, 2.11, 2.22, 2.33]
            speed_lookup_i = min(game_level, len(level_speed)-1)
            theme_bg_sound.stretch_factor = level_speed[speed_lookup_i] - 0.22

    def get_game_level(self) -> int:
        return self._game_level

    def reset(self, start=True):
        theme_bg_sound.stretch_factor = 1
        theme_bg_sound.pitch_shift = 0

        self.grid = [[None for j in range(self.width)]
                     for i in range(self.height)]
        self.last_game_tick_ms = 0
        self.game_score = 0
        self.game_lines_cleared = 0
        self._game_level = None
        self._set_game_level(0)
        self.game_is_over = False
        self.current_tetromin = None
        self.next_tetromin = None
        self.set_next_tetromin()
        if start:
            self.start()

    def is_muted(self) -> bool:
        return self._muted

    def mute(self):
        if self._muted:
            return
        self._muted = True
        mute_pygame_sounds()

    def unmute(self):
        if not self._muted:
            return
        self._muted = False
        unmute_pygame_sounds()

    def start(self):
        self.last_game_tick_ms = ms_now()
        sound_start.play()
        sampler.play(theme_bg_sound)

    def get_current_game_tick_ms_T(self):
        game_level = self.get_game_level()
        game_speed_seconds = (0.8-game_level*0.007)**game_level
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
        self.tetromin_down(ignore_move_sound=True)

    def set_next_tetromin(self):
        def generate_next_tetromin():
            return tetromin_list[int(random()*len(tetromin_list))]()

        self.current_tetromin = {
            'tetro': self.next_tetromin or generate_next_tetromin(),
            'x': self.width//2 - 1,
            'y': 1
        }

        self.next_tetromin = generate_next_tetromin()
        # checks if current tetromin that was placed is in red zone or "end game"
        if self.current_tetromin and self.does_current_tetromin_collide() and self.is_current_tetromin_in_spawn_area():
            self.game_is_over = True
            sound_gameover.play()
            theme_bg_sound.pitch_shift = 0.25
            theme_bg_sound.stretch_factor = 0.25
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
        sound_combo = [None, sound_combo1, sound_combo2,
                       sound_combo3, sound_combo4][min(lines_cleared, 4)]
        if sound_combo:
            sound_combo.play()
        self.game_lines_cleared += lines_cleared
        self._set_game_level(self.game_lines_cleared // 10)

    def set_level(self, level: int):
        self.reset(True)
        self.game_lines_cleared = 10 * level
        self._set_game_level(level)

    def calculate_break_rows_score(self, lines_combo: int) -> int:
        max_lines_combo = 4
        lines_multiplier = [0, 40, 100, 300, 1200]  # 1 2 3 and 4
        lines_combo = min(lines_combo, max_lines_combo)
        return lines_multiplier[lines_combo] * (self.get_game_level() + 1)

    def burn_current_tetromin_into_grid(self):
        tetro, tx, ty = self.unpack_current_tetromin()
        tetro_grid = tetro.current_grid()
        for y in range(tetro.height()):
            for x in range(tetro.width()):
                if tetro_grid[y][x]:
                    self.grid[ty+y][tx+x] = tetro.color

        self.break_full_rows()

    @disable_on_gameover
    def tetromin_down(self, process_logic_on_collision=True, ignore_move_sound=False):
        self.skip_game_tick()
        self.current_tetromin['y'] += 1
        if not ignore_move_sound:
            sound_move.play()
        if collides := self.does_current_tetromin_collide():
            print('play hadrdrop')
            sound_harddrop.play()
            self.current_tetromin['y'] -= 1
            if process_logic_on_collision:
                self.burn_current_tetromin_into_grid()
                self.set_next_tetromin()
        return collides

    @disable_on_gameover
    def tetromin_left(self, ignore_move_sound=False):
        self.current_tetromin['x'] -= 1
        if collides := self.does_current_tetromin_collide():
            self.current_tetromin['x'] += 1
            not ignore_move_sound and sound_invalid.play()
        else:
            not ignore_move_sound and sound_move.play()
        return collides

    @disable_on_gameover
    def tetromin_right(self, ignore_move_sound=False):
        self.current_tetromin['x'] += 1
        if collides := self.does_current_tetromin_collide():
            self.current_tetromin['x'] -= 1
            not ignore_move_sound and sound_invalid.play()
        else:
            not ignore_move_sound and sound_move.play()
        return collides

    @disable_on_gameover
    def tetromin_rotate(self):
        self.current_tetromin['tetro'].rotate()
        if collides := self.does_current_tetromin_collide():
            self.current_tetromin['tetro'].rotate(backward=True)
            sound_invalid.play()
        else:
            sound_rotate.play()
        return collides

    @disable_on_gameover
    def tetromin_harddrop(self):
        hard_drop_points = 0
        while not self.tetromin_down(ignore_move_sound=True):
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
