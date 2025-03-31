from typing import List, Literal, Tuple
from manim import BLUE, DOWN, LEFT, ORIGIN, RED, RIGHT, UP, Add, Arrow, Circle, Create, FadeIn, LaggedStart, Rectangle, Scene, Transform, Uncreate, VGroup, Text
from puzzle import Cell, CellScanner, Game, Grid, Hint, HintSet, Line, SegmentSquares, SquareState, gen_square_mark

class TestCell(Scene):
    def construct(self):
        cell = Cell()
        self.play(Create(cell))
        self.wait(1)
        self.play(cell.set_state(SquareState.FILLED), subcaption="Filled")
        self.wait(1)
        self.play(cell.set_state(SquareState.UNKOWN), subcaption="Unknown")
        self.wait(1)
        self.play(cell.set_state(SquareState.EMPTY), subcaption="Empty")
        self.wait(1)
        self.play(cell.set_state(SquareState.FILLED), subcaption="Filled")
        self.wait(1)
        self.play(cell.set_state(SquareState.EMPTY), subcaption="Empty")


class TestGrid(Scene):
    def construct(self):
        grid = Grid(5, 5)
        self.play(Create(grid))
        self.play(grid.set_cell_state(0, 0, SquareState.FILLED))
        self.play(grid.set_cell_state(0, 1, SquareState.FILLED))
        self.play(grid.set_cell_state(1, 0, SquareState.FILLED))
        self.play(grid.set_cell_state(4, 4, SquareState.EMPTY))

class TestHint(Scene):
    def construct(self):
        # Create a horizontal hint with 5 segments, values [3, 1, 2]
        # This will result in: [empty, empty, 3, 1, 2]
        horizontal_hint = Hint([3, 1, 2], 5, True)
        horizontal_hint2 = Hint([3, 1, 2, 4, 7], 5, True)

        # Create a vertical hint with 4 segments, values [1, 1]
        # This will result in: [empty, empty, 1, 1] from top to bottom
        vertical_hint = Hint([1, 1], 4, False)
        bigger_numbers = Hint([3, 13, 300], 3, True)
        self.play(Create(horizontal_hint))
        self.wait()
        self.play(Uncreate(horizontal_hint))
        self.play(Create(horizontal_hint2))
        self.wait()
        self.play(Uncreate(horizontal_hint2))
        self.play(Create(vertical_hint))
        self.wait()
        self.play(Uncreate(vertical_hint))
        self.play(Create(bigger_numbers))
        self.wait()
        self.play(Uncreate(bigger_numbers))

class TestHintSet(Scene):
    def construct(self):
        # Create row hints for a nonogram
        row_hints = [
            [3],
            [1, 1],
            [2]
        ]
        row_hint_set = HintSet(row_hints, direction="row")

        # Create column hints for the same nonogram
        col_hints = [
            [2],
            [1, 1],
            [2]
        ]
        col_hint_set = HintSet(col_hints, direction="col")
        self.play(Create(row_hint_set))
        self.wait()
        self.play(Uncreate(row_hint_set))
        self.play(Create(col_hint_set))
        self.wait()
        self.play(Uncreate(col_hint_set))

class TestGame(Scene):
    def construct(self):
        # Create row hints for a nonogram
        row_hints = [
            [3],
            [1, 1],
            [1]
        ]

        # Create column hints for the same nonogram
        col_hints = [
            [2],
            [1, 1],
            [2]
        ]
        game = Game(row_hints, col_hints)
        self.play(Create(game))
        self.play(LaggedStart(*game.grid.set_line([SquareState.FILLED, SquareState.FILLED, SquareState.FILLED], 0, "row"), lag_ratio=0.15))
        self.play(LaggedStart(*game.grid.set_line([SquareState.FILLED, SquareState.FILLED, SquareState.EMPTY], 0, "col"), lag_ratio=0.15))
        self.play(LaggedStart(*game.grid.set_line([SquareState.FILLED, SquareState.FILLED, SquareState.EMPTY], 2, "col"), lag_ratio=0.15))
        self.play(LaggedStart(*game.grid.set_line([SquareState.FILLED, SquareState.EMPTY, SquareState.FILLED], 1, "row"), lag_ratio=0.15))
        self.play(LaggedStart(*game.grid.set_line([SquareState.EMPTY, SquareState.FILLED, SquareState.EMPTY], 2, "row"), lag_ratio=0.15))
        self.wait(3)


def parse_solution_file(file_name) -> Tuple[Game, List[Tuple[List[SquareState], int, Literal["row"] | Literal["col"]]]]:
    """
3 # Row Hints
1 1
1

2 # Col Hints
1 1
2

0 row o o o # Solution
0 col o o x
2 col o o x
1 row o x o
2 row x o x
    """
    def parse_square(square: str) -> SquareState:
        match square.strip():
            case "o":
                return SquareState.FILLED
            case "x":
                return SquareState.EMPTY
            case "_":
                return SquareState.UNKOWN
            case _:
                raise ValueError(f"{square} is not 'o', 'x', or '_'")

    with open(file_name, "r") as f:
        row_hint = []
        while (line := f.readline()) != "\n":
            row_hint.append(list(map(lambda x: int(x), line.split(" "))))
        col_hint = []
        while (line := f.readline()) != "\n":
            col_hint.append(list(map(lambda x: int(x), line.split(" "))))
        solution = []
        while (line := f.readline()):
            line_list = line.split(" ")
            i = int(line_list[0])
            if line_list[1] not in {"row", "col"}:
                raise ValueError("Direction must be 'row' or 'col'")
            direction = line_list[1]
            line = list(map(parse_square, line_list[2:]))
            solution.append((line, i, direction))

    return (Game(row_hint, col_hint, 1), solution)

class VisualizeSolution(Scene):
    def construct(self):
        game, solution = parse_solution_file("solution.txt")
        # game.shift(DOWN * 1.3)
        game.move_to(ORIGIN)
        game.scale_to_fit_height(7.5)
        self.play(Create(game))
        for solution_line in solution:
            try:
                self.play(LaggedStart(*game.grid.set_line(*solution_line), lag_ratio=0.15))
            except ValueError:
                pass
        self.wait(3)

class OverlapAlg(Scene):
    def construct(self):
        all_obj = VGroup()
        initial_line = Line([3, 4], length=10)
        initial_line.set_hint_color(0, BLUE)
        initial_line.set_hint_color(1, RED)

        left_line = initial_line.copy()


        left_line.create_segments(3, 4)

        left_line.set_seg_color(0, BLUE)
        left_line.set_seg_color(1, RED)

        left_line.move_segment_to(0, 0)
        left_line.move_segment_to(1, 4)

        solution_line = left_line.copy()

        right_line = left_line.copy()

        # initial_text = Text("Initial State")
        # left_text = Text("Left Solution")
        # right_text = Text("Right Solution")
        # sol_text = Text("New Overlap")

        initial_line.shift(UP*2.2)
        right_line.shift(DOWN*1.1)
        solution_line.shift(3.3 * DOWN)

        # initial_text.next_to(initial_line, LEFT)
        # left_text.next_to(left_line, LEFT)
        # right_text.next_to(right_line, LEFT)
        # sol_text.next_to(solution_line, LEFT)

        scanner = CellScanner(left_line.squares_group[0], solution_line.squares_group[0])
        scanner.set_z_index(3)

        whacky_arrow = Arrow(start=right_line.get_critical_point(DOWN), end=solution_line.get_critical_point(UP))
        whacky_arrow2 = Arrow(start=initial_line.get_critical_point(DOWN), end=left_line.get_critical_point(UP))

        # all_obj.add(initial_line, left_line, right_line, solution_line, scanner, initial_text, left_text, right_text, sol_text, whacky_arrow, whacky_arrow2)
        all_obj.add(initial_line, left_line, right_line, solution_line, scanner, whacky_arrow, whacky_arrow2)
        all_obj.move_to(ORIGIN)
        original_width = all_obj.width
        # all_obj.scale_to_fit_width(14)
        ratio = all_obj.width/original_width

        self.play(FadeIn(initial_line))
        self.play(FadeIn(left_line, whacky_arrow2, shift=DOWN*1.1))
        self.play(FadeIn(right_line, shift=DOWN*1.1))
        self.play(FadeIn(solution_line, whacky_arrow, shift=DOWN*1.1))
        # self.play(Create(scanner))

        self.play(right_line.animate.move_segment_to(1, 6))
        self.play(right_line.animate.move_segment_to(0, 2))
        self.wait(3)
        return

        self.play(scanner.animate.shift_by_cell(RIGHT*ratio))
        self.play(scanner.animate.shift_by_cell(RIGHT*ratio))

        top_blue_copy1 = left_line.segment_group[0][2].copy()
        bot_blue_copy1 = right_line.segment_group[0][0].copy()

        sol_square1 = gen_square_mark(ratio, 0.8)
        sol_square1.set_color(BLUE)
        sol_square1.move_to(solution_line.squares_group[2])
        self.play(Transform(top_blue_copy1, sol_square1), Transform(bot_blue_copy1, sol_square1))

        self.play(scanner.animate.shift_by_cell(RIGHT*ratio))
        self.play(scanner.animate.shift_by_cell(RIGHT*ratio))
        self.play(scanner.animate.shift_by_cell(RIGHT*ratio))
        self.play(scanner.animate.shift_by_cell(RIGHT*ratio))

        top_blue_copy2 = left_line.segment_group[1][2].copy()
        bot_blue_copy2 = right_line.segment_group[1][0].copy()

        sol_square2 = gen_square_mark(ratio, 0.8)
        sol_square2.set_color(RED)
        sol_square2.move_to(solution_line.squares_group[6])
        self.play(Transform(top_blue_copy2, sol_square2), Transform(bot_blue_copy2, sol_square2))

        self.play(scanner.animate.shift_by_cell(RIGHT*ratio))

        top_blue_copy3 = left_line.segment_group[1][3].copy()
        bot_blue_copy3 = right_line.segment_group[1][1].copy()

        sol_square3 = gen_square_mark(ratio, 0.8)
        sol_square3.set_color(RED)
        sol_square3.move_to(solution_line.squares_group[7])
        self.play(Transform(top_blue_copy3, sol_square3), Transform(bot_blue_copy3, sol_square3))

        self.play(scanner.animate.shift_by_cell(RIGHT*ratio))
        self.play(scanner.animate.shift_by_cell(RIGHT*ratio))
        self.play(Uncreate(scanner))
        print(all_obj.height)
        self.wait(3)
