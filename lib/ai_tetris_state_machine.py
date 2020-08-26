from lib.tetris_state_machine import TetrisStateMachine


class AiTetrisStateMachine(TetrisStateMachine):

    def generate_best_fit_path_commands(self):
        if self.game_is_over:
            return []
        return self._ai_fit_best_grid([])[1]

    def _ai_try_down(self, reversed_success_op=False):
        if reversed_success_op:
            self.current_tetromin['y'] -= 1
            return

        self.current_tetromin['y'] += 1
        if collides := self.does_current_tetromin_collide():
            self.current_tetromin['y'] -= 1
        return not collides

    def _ai_try_left(self, reversed_success_op=False):
        if reversed_success_op:
            self.current_tetromin['x'] += 1
            return

        self.current_tetromin['x'] -= 1
        if collides := self.does_current_tetromin_collide():
            self.current_tetromin['x'] += 1
        return not collides

    def _ai_try_right(self, reversed_success_op=False):
        if reversed_success_op:
            self.current_tetromin['x'] -= 1
            return

        self.current_tetromin['x'] += 1
        if collides := self.does_current_tetromin_collide():
            self.current_tetromin['x'] -= 1
        return not collides

    def _ai_try_rotate(self, reversed_success_op=False):
        if reversed_success_op:
            self.current_tetromin['tetro'].rotate(backward=True)
            return

        self.current_tetromin['tetro'].rotate()
        if collides := self.does_current_tetromin_collide():
            self.current_tetromin['tetro'].rotate(backward=True)
        return not collides

    def _ai_fit_best_grid(self, previous_ops, prev_sym=None, dynamic_grid=None):
        # "Brute force till you make it :^)"
        # (Please note i was a bit drunk when i wrote this.)
        if not dynamic_grid:
            dynamic_grid = [[[None for j in range(self.width)]
                             for i in range(self.height)] for r in range(4)]

        cty = self.current_tetromin['y']
        ctx = self.current_tetromin['x']
        ctr = self.current_tetromin['tetro'].current_rotation_i()

        if dg_lookup := dynamic_grid[ctr][cty][ctx]:
            return dg_lookup

        # [... [SCORE, [op1,op2,op3,...,opN], rotation_i] ... ]
        evals = []
        rotate_success_cnt = 0
        solutions = []

        for rotation_count in range(self.current_tetromin['tetro'].defined_rotations()):
            ctr = self.current_tetromin['tetro'].current_rotation_i()
            for test_method, op, sym in [
                (self._ai_try_down, lambda: self.tetromin_down(
                    ignore_move_sound=True), 'D'),
                (self._ai_try_left, lambda: self.tetromin_left(
                    ignore_move_sound=True), 'L'),
                (self._ai_try_right, lambda: self.tetromin_right(
                    ignore_move_sound=True), 'R')
            ]:

                # if tetromin was going left, dont allow to push it right, and vice versa!
                if (sym == 'R' and prev_sym == 'L') or (sym == 'L' and prev_sym == 'R'):
                    continue

                if test_method():
                    rec_eval = self._ai_fit_best_grid(
                        previous_ops=[*previous_ops, *([self.tetromin_rotate]*rotate_success_cnt), op], prev_sym=sym, dynamic_grid=dynamic_grid)
                    evals.append([*rec_eval, ctr])
                    test_method(reversed_success_op=True)

                elif test_method == self._ai_try_down:
                    finish_op = self.tetromin_down  # finish op to end the turn!
                    final_ops = [
                        *previous_ops, *([self.tetromin_rotate] * rotate_success_cnt), finish_op]
                    grid = self.get_render_grid()  # burn tetromin into grid!
                    grid_eval = self._ai_rate_grid(grid)
                    rate = [grid_eval, final_ops, ctr]
                    # [SCORE, [op1,op2,op3,...,opN]]
                    evals.append(rate)

            # minimize the error for current rotation!
            best_match = min(evals, key=lambda eval: eval[0])
            solutions.append(best_match)
            dynamic_grid[ctr][cty][ctx] = best_match
            evals = []
            if self._ai_try_rotate():
                rotate_success_cnt += 1

        for _ in range(rotate_success_cnt):
            self._ai_try_rotate(reversed_success_op=True)
        # minimize the error and find the best solution from all rotations!
        return min(solutions, key=lambda eval: eval[0])

    def _ai_rate_grid(self, grid):
        # make copy of grid so we don't fuck something outside this function.
        grid = [row[:] for row in grid]

        def column_max_i(column, grid):
            for y in range(self.height):
                if grid[y][column] is not None:
                    return y
            return self.height

        def break_full_rows(grid):
            def is_row_full(row, grid) -> bool:
                for x in range(self.width):
                    if not grid[row][x]:
                        return False
                return True

            def remove_row(row, grid):
                while row >= 0:
                    for x in range(self.width):
                        grid[row][x] = None
                        if row-1 >= 0:
                            grid[row][x] = grid[row-1][x]
                    row -= 1

            y = self.height - 1
            # go up the rows!
            while y >= 0:
                if is_row_full(y, grid):
                    remove_row(y, grid)
                else:
                    y -= 1

        def glow_error(sr, grid):
            err = 0

            def val(it):
                return 1 if it else 0

            for y in range(sr, self.height):
                for x in range(self.width):
                    if not grid[y][x]:
                        l = val(grid[y][x-1] if x-1 >= 0 else 0)
                        r = val(grid[y][x+1] if x+1 < self.width else 0)
                        t = val(grid[y-1][x] if y-1 >= 0 else 0) * 5
                        b = val(grid[y+1][x] if y+1 < self.height else 0) * 5
                        # +b (kinda acting better without bottom applied.. need to write some tests to approve this hypothesis)
                        err += l+r+t

            return err

        top_before = min([column_max_i(x, grid) for x in range(self.width)])
        break_full_rows(grid)
        top = min([column_max_i(x, grid) for x in range(self.width)])

        if top == self.height:
            return 0

        if top - top_before >= 1:
            return 4 - (top - top_before)

        return glow_error(top, grid)
