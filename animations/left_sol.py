from typing import Literal
from manim import BLUE, DOWN, UP, Arrow, Scene, Text, VGroup

from puzzle import LabeledPointer, Line, SegPlacer, SquareState


class SegPos(Scene):
    def construct(self):
        line = Line([5], length=10)
        line.set_hint_color(0, BLUE)
        line.create_segments(5)
        line.move_segment_to(0, 2)
        line.set_seg_color(0, BLUE)
        numbers = VGroup()
        for i in range(10):
            number = Text(str(i))
            number.scale_to_fit_height(0.5)
            number.next_to(line.squares_group[i], UP)
            numbers.add(number.copy())
        arrow = Arrow(start=DOWN/2, end=UP).next_to(line.squares_group[2], DOWN)
        self.add(line, numbers, arrow)


"""
from enum import Enum
from typing import List
# Represents the state of an individual square
# An enum type can be one of any of the variants defined
class SquareState(Enum):
    UNKOWN = 0
    FILLED = 1
    EMPTY = 2

# A segment length in a hint
type Segment = int

def find_left_sol(hint: List[Segment], line: List[SquareState]) -> List[SquareState]:
    next_seg_pos = 0
    for segment in hint:
        for i in range(next_seg_pos, next_seg_pos + segment):
            line[i] = SquareState.FILLED
        next_seg_pos += segment + 1

    return line
"""

class BasicSol(Scene):
    def construct(self):
        segs = [1, 2, 3]
        seg_placer = SegPlacer(segs, length=10)

        arrow = LabeledPointer("Next Position")
        arrow.next_to(seg_placer.squares_group[0], DOWN)
        self.add(seg_placer, arrow)

        self.play(seg_placer.animate.move_segment_to(0, 0))
        self.play(arrow.animate.next_to(seg_placer.squares_group[2], DOWN), seg_placer.squares_group[1].set_state(SquareState.EMPTY))

        self.play(seg_placer.animate.move_segment_to(1, 2))
        self.play(arrow.animate.next_to(seg_placer.squares_group[5], DOWN), seg_placer.squares_group[4].set_state(SquareState.EMPTY))

        self.play(seg_placer.animate.move_segment_to(2, 5))
        self.play(*(seg_placer.squares_group[i].set_state(SquareState.EMPTY) for i in range(8, 10)))
