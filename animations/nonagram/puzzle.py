from enum import Enum
from typing import Generator, List, Literal
from manim import BLUE, DOWN, LEFT, RIGHT, UP, WHITE, Animation, AnimationGroup, Circle, Cross, FadeIn, FadeOut, Mobject, ParsableManimColor, Rectangle, Square, Succession, SurroundingRectangle, Text, VGroup, VMobject, np
from manim.typing import Point3DLike, Vector3D

class SquareState(Enum):
    UNKOWN = 0
    FILLED = 1
    EMPTY = 2

def gen_square_mark(outer_size, inner_ratio = 0.7):
    return Square(side_length=outer_size * inner_ratio, color=WHITE, z_index=1, fill_opacity=1, stroke_opacity=0)

CELL_SIZE = 1.0
class Cell(VMobject):
    def __init__(self, cell_size = CELL_SIZE, **kwargs) -> None:
        super().__init__(**kwargs)
        self.cell_size = cell_size

        self.state = SquareState.UNKOWN
        self.background = Square(side_length=cell_size, z_index=0)
        self.x_mark = Cross(self.background, z_index=2, scale_factor=0.7)
        self.square_mark = gen_square_mark(cell_size)

        self.add(self.background, self.x_mark, self.square_mark)
        self.square_mark.set_opacity(0)
        self.x_mark.set_opacity(0)

        self.x_mark.move_to(self.background.get_center())
        self.square_mark.move_to(self.background.get_center())


    def set_state_no_animate(self, state: SquareState) -> None:
        old_state = self.state
        self.state = state

        # I dont know why these need to be called in this function
        self.x_mark.move_to(self.background.get_center())
        self.square_mark.move_to(self.background.get_center())

        match (old_state, state):
            case (SquareState.UNKOWN, SquareState.FILLED):
                self.square_mark.set_opacity(1)
            case (SquareState.UNKOWN, SquareState.EMPTY):
                self.x_mark.set_opacity(1)
            case (SquareState.FILLED, SquareState.UNKOWN):
                self.square_mark.set_opacity(0)
            case (SquareState.EMPTY, SquareState.UNKOWN):
                self.x_mark.set_opacity(0)
            case (SquareState.FILLED, SquareState.EMPTY):
                self.square_mark.set_opacity(0)
                self.x_mark.set_opacity(1)
            case (SquareState.EMPTY, SquareState.FILLED):
                self.x_mark.set_opacity(0)
                self.square_mark.set_opacity(1)
        return None


    def set_state(self, state: SquareState) -> Animation | None:
        old_state = self.state
        self.state = state

        # I dont know why these need to be called in this function
        self.x_mark.move_to(self.background.get_center())
        self.square_mark.move_to(self.background.get_center())

        match (old_state, state):
            case (SquareState.UNKOWN, SquareState.FILLED):
                return self.square_mark.animate.set_opacity(1)
            case (SquareState.UNKOWN, SquareState.EMPTY):
                return self.x_mark.animate.set_opacity(1)
            case (SquareState.FILLED, SquareState.UNKOWN):
                return self.square_mark.animate.set_opacity(0)
            case (SquareState.EMPTY, SquareState.UNKOWN):
                return self.x_mark.animate.set_opacity(0)
            case (SquareState.FILLED, SquareState.EMPTY):
                return Succession(
                    self.square_mark.animate.set_opacity(0),
                    self.x_mark.animate.set_opacity(1),
                )
            case (SquareState.EMPTY, SquareState.FILLED):
                return Succession(
                    self.x_mark.animate.set_opacity(0),
                    self.square_mark.animate.set_opacity(1),
                )
        return None


class Grid(VMobject):
    def __init__(self, rows: int, cols: int, cell_size = CELL_SIZE, **kwargs):
        super().__init__(**kwargs)

        self.rows = rows
        self.cols = cols
        self.squares_group = VGroup()
        self.squares_group.add(*[Cell(cell_size) for _ in range(rows * cols)])
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
    def __init__(self, value: int | None, cell_size = CELL_SIZE, **kwargs):
        super().__init__(**kwargs)

        self.value = value
        self.background = Square(side_length=cell_size, z_index=0, background_stroke_color=(150, 150, 150))

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
            scaling_factor = (cell_size * 0.7) / max_dimension
            self.text.scale(scaling_factor)

            # Position text in the center of the square
            self.text.move_to(self.background.get_center())

            # Add the text to the VMobject
            self.add(self.text)

class Hint(VMobject):
    def __init__(self, values: List[int], length: int, horizontal: bool, cell_size = CELL_SIZE, **kwargs):
        super().__init__(**kwargs)

        if len(values) > length:
            raise ValueError("values was longer than length")

        # Calculate padding needed
        padding_count = length - len(values)

        # Create a VGroup to hold all hint segments
        self.segments = VGroup()

        # Add empty hint segments for padding
        for _ in range(padding_count):
            self.segments.add(HintSegment(None, cell_size))

        # Add hint segments with values
        for value in values:
            self.segments.add(HintSegment(value, cell_size))

        # Arrange segments based on direction
        if horizontal:
            self.segments.arrange(RIGHT, buff=0)
        else:
            self.segments.arrange(DOWN, buff=0)

        # Add all segments to the VMobject
        self.add(self.segments)

# For demo purposes, used in place of setting the state of a cell
# Useful for when you need some squares not directly attached to a cell so you can move them freely
class SegmentSquares(VGroup):
    def __init__(self, length, outer_size=CELL_SIZE, inner_ratio = 0.8):
        super().__init__()
        self.outer_size = outer_size
        self.inner_ratio = inner_ratio
        self.add(*[gen_square_mark(outer_size, inner_ratio) for _ in range(length)])
        self.arrange(RIGHT, buff=outer_size*(1-inner_ratio))
        self.offset = - (self[0].get_center() - self.get_center())

    # Overriden to move from the center of the first square
    def move_to(self, obj: Point3DLike | Mobject, *args, **kwargs):
        if isinstance(obj, Mobject):
            super().move_to(obj.get_center() + self.offset, *args, **kwargs)
        else:
            super().move_to(obj + self.offset, *args, **kwargs)

# Mostly just used for demo purposes
class Line(VMobject):
    def __init__(self, hint: list[int], initial_line: List[Cell] | None = None, length: int | None = None, cell_size = CELL_SIZE, **kwargs):
        super().__init__(**kwargs)
        self.hint = hint
        self.hint_obj = Hint(hint, len(hint), True, cell_size)
        self.squares_group = VGroup()
        self.segment_group = VGroup()
        self.xs_group = VGroup()
        self.cell_size = cell_size
        if not initial_line:
            if length is None:
                raise ValueError("initial_line or length must be specified")
            self.squares_group.add(*[Cell() for _ in range(length)])
            self.length = length
        else:
            self.length = len(initial_line)
            self.squares_group.add(*initial_line)
        self.squares_group.arrange(RIGHT, buff=0)
        self.hint_obj.next_to(self.squares_group, LEFT, buff=0)
        full_group = VGroup(self.hint_obj, self.squares_group)
        full_group.center()
        self.add(self.hint_obj, self.squares_group, self.segment_group, self.xs_group)

    def create_segments(self, *segment_lengths: int):
        for length in segment_lengths:
            self.segment_group.add(SegmentSquares(length))

    def add_segment(self, *segments: SegmentSquares):
        for seg in segments:
            self.segment_group.add(seg)

    def move_segment_to(self, seg_index: int, square_index: int):
        self.segment_group[seg_index].move_to(self.squares_group[square_index])

    def slide_segment(self, seg_index: int, vector: Vector3D):
        return self.segment_group[seg_index].animate.shift(vector*self.cell_size)

    def set_hint_color(self, hint_index: int, color: ParsableManimColor):
        self.hint_obj.segments[hint_index].text.set_color(color)

    def set_seg_color(self, seg_index: int, color: ParsableManimColor):
        self.segment_group[seg_index].set_color(color)

    def set_xs(self, indices):
        for i in indices:
            cross = Cross(self.squares_group[i], z_index=2, scale_factor=0.8)
            cross.move_to(self.squares_group[i])
            self.xs_group.add(cross)


class HintSet(VMobject):
    def __init__(self, hint_values: List[List[int]], direction: Literal["row"] | Literal["col"], cell_size = CELL_SIZE, **kwargs):
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
            hint = Hint(values, max_length, hint_direction, cell_size)
            self.hints.add(hint)

        # Arrange the hints appropriately
        if len(self.hints) > 0:
            self.hints.arrange(arrangement_direction, buff=0)

        # Add all hints to the VMobject
        self.add(self.hints)

# For demo purposes
# Used to demostrate a scanner that scans over the cells of a line
# All cells should be the same size
class CellScanner(SurroundingRectangle):
    def __init__(self, *cells: Cell, **kwargs):
        self.cell_size = cells[0].cell_size
        super().__init__(*cells, **kwargs)

    def shift_by_cell(self, *vectors: Vector3D):
        self.shift(*(vector*self.cell_size for vector in vectors))

class Game(VMobject):
    def __init__(self, row_hints: List[List[int]], col_hints: List[List[int]], cell_size = CELL_SIZE, **kwargs):
        super().__init__(**kwargs)

        self.grid = Grid(len(row_hints), len(col_hints), cell_size)
        self.row_hint_set = HintSet(row_hints, "row", cell_size)
        self.col_hint_set = HintSet(col_hints, "col", cell_size)
        self.row_hint_set.next_to(self.grid, LEFT, buff=0)
        self.col_hint_set.next_to(self.grid, UP, buff=0)
        self.add(self.grid, self.row_hint_set, self.col_hint_set)
