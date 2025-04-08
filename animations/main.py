from typing import List, Literal, Tuple
from manim import ORIGIN, Create, LaggedStart, Scene, Uncreate
from puzzle import Cell, Game, Grid, Hint, HintSet, SquareState

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

