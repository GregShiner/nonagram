from enum import Enum
import readline
from typing import Generator, List, Literal, Tuple
from manim import DOWN, LEFT, PI, RIGHT, UP, WHITE, Animation, AnimationGroup, Arc, Circle, Create, Cross, FadeIn, FadeOut, LaggedStart, Rectangle, Scene, Square, Succession, Text, Uncreate, VGroup, VMobject

class SquareState(Enum):
    UNKOWN = 0
    FILLED = 1
    EMPTY = 2


CELL_SIZE = .525
class Cell(VMobject):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.state = SquareState.UNKOWN
        self.background = Square(side_length=CELL_SIZE, z_index=0)
        self.x_mark = Cross(self.background, z_index=2, scale_factor=0.8)
        self.square_mark = Square(side_length=CELL_SIZE * 0.8, color=WHITE, z_index=1, fill_opacity=1, stroke_opacity=0)

        self.add(self.background)

        self.x_mark.move_to(self.background.get_center())
        self.square_mark.move_to(self.background.get_center())


    def set_state(self, state: SquareState) -> Animation | None:
        old_state = self.state
        self.state = state

        # I dont know why these need to be called in this function
        self.x_mark.move_to(self.background.get_center())
        self.square_mark.move_to(self.background.get_center())

        match (old_state, state):
            case (SquareState.UNKOWN, SquareState.FILLED):
                return FadeIn(self.square_mark)
            case (SquareState.UNKOWN, SquareState.EMPTY):
                return FadeIn(self.x_mark)
            case (SquareState.FILLED, SquareState.UNKOWN):
                return FadeOut(self.square_mark)
            case (SquareState.EMPTY, SquareState.UNKOWN):
                return FadeOut(self.x_mark)
            case (SquareState.FILLED, SquareState.EMPTY):
                return Succession(FadeOut(self.square_mark), FadeIn(self.x_mark))
            case (SquareState.EMPTY, SquareState.FILLED):
                return Succession(FadeOut(self.x_mark), FadeIn(self.square_mark))
        return None


class Grid(VMobject):
    def __init__(self, rows: int, cols: int, **kwargs):
        super().__init__(**kwargs)

        self.rows = rows
        self.cols = cols
        self.squares_group = VGroup()
        self.squares_group.add(*[Cell() for _ in range(rows * cols)])
        self.squares_group.arrange_in_grid(rows=rows, cols=cols, buff=0)

        self.add(self.squares_group)

    def get_cell(self, row: int, col: int) -> Cell:
        if row < 0 or row >= self.rows or col < 0 or col >= self.cols:
            raise IndexError(f"Position ({row}, {col}) is outside the grid bounds")

        index = row * self.cols + col
        return self.squares_group[index]

    def set_cell_state(self, row: int, col: int, state: SquareState) -> Animation | None:
        cell = self.get_cell(row, col)
        return cell.set_state(state)

    def set_line(self, line: List[SquareState | None], i: int, direction: Literal["row"] | Literal["col"]) -> Generator[Animation]:
        for (j, square) in enumerate(line):
            if not square:
                continue

            if direction == "row":
                animation = self.set_cell_state(i, j, square)
            else:
                animation = self.set_cell_state(j, i, square)

            if animation:
                yield animation # YA THATS RIGHT, A GENERATOR


class HintSegment(VMobject):
    def __init__(self, value: int | None, **kwargs):
        super().__init__(**kwargs)

        self.value = value
        self.background = Square(side_length=CELL_SIZE, z_index=0, background_stroke_color=(150, 150, 150))

        # Add the background to the VMobject
        self.add(self.background)

        # If a value was provided, create and add text
        if value is not None:
            # Create text with the value
            self.text = Text(str(value), z_index=1)

            # Scale text to fit within the square (with some padding)
            text_width = self.text.width
            text_height = self.text.height
            max_dimension = max(text_width, text_height)
            scaling_factor = (CELL_SIZE * 0.7) / max_dimension
            self.text.scale(scaling_factor)

            # Position text in the center of the square
            self.text.move_to(self.background.get_center())

            # Add the text to the VMobject
            self.add(self.text)

class Hint(VMobject):
    def __init__(self, values: List[int], length: int, horizontal: bool, **kwargs):
        super().__init__(**kwargs)

        if len(values) > length:
            raise ValueError("values was longer than length")

        # Calculate padding needed
        padding_count = length - len(values)

        # Create a VGroup to hold all hint segments
        self.segments = VGroup()

        # Add empty hint segments for padding
        for _ in range(padding_count):
            self.segments.add(HintSegment(None))

        # Add hint segments with values
        for value in values:
            self.segments.add(HintSegment(value))

        # Arrange segments based on direction
        if horizontal:
            self.segments.arrange(RIGHT, buff=0)
        else:
            self.segments.arrange(DOWN, buff=0)

        # Add all segments to the VMobject
        self.add(self.segments)

class HintSet(VMobject):
    def __init__(self, hint_values: List[List[int]], direction: Literal["row"] | Literal["col"], **kwargs):
        super().__init__(**kwargs)

        # Find the maximum length of any hint list
        max_length = 0
        max_length = max(len(hint_list) for hint_list in hint_values)

        # Create a VGroup to hold all hints
        self.hints = VGroup()

        # Determine hint direction and arrangement based on the HintSet direction
        if direction == "row":
            hint_direction = True
            arrangement_direction = DOWN
        elif direction == "col":
            hint_direction = False
            arrangement_direction = RIGHT

        # Create a Hint for each set of values
        for values in hint_values:
            hint = Hint(values, max_length, hint_direction)
            self.hints.add(hint)

        # Arrange the hints appropriately
        if len(self.hints) > 0:
            self.hints.arrange(arrangement_direction, buff=0)

        # Add all hints to the VMobject
        self.add(self.hints)

class Game(VMobject):
    def __init__(self, row_hints: List[List[int]], col_hints: List[List[int]], **kwargs):
        super().__init__(**kwargs)

        self.grid = Grid(len(row_hints), len(col_hints))
        self.row_hint_set = HintSet(row_hints, "row")
        self.col_hint_set = HintSet(col_hints, "col")
        self.row_hint_set.next_to(self.grid, LEFT, buff=0)
        self.col_hint_set.next_to(self.grid, UP, buff=0)
        self.add(self.grid, self.row_hint_set, self.col_hint_set)

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

    return (Game(row_hint, col_hint), solution)

class VisualizeSolution(Scene):
    def construct(self):
        game, solution = parse_solution_file("solution.txt")
        game.shift(DOWN * 1.3)
        self.play(Create(game))
        for solution_line in solution:
            try:
                self.play(LaggedStart(*game.grid.set_line(*solution_line), lag_ratio=0.15))
            except ValueError:
                pass
        self.wait(3)

class PeePee(Scene):
    def construct(self):
        shaft = Rectangle(width=1, height=3)
        shaft_top_arc = Arc(angle=PI, radius=0.5).next_to(shaft, UP*0.01)
        left_nut = Circle().shift(DOWN*2.4 + LEFT)
        right_nut = Circle().shift(DOWN*2.4 + RIGHT)
        self.play(Create(shaft), Create(shaft_top_arc), Create(left_nut), Create(right_nut))
        self.wait()
