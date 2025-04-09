from manim import BLUE, DOWN, UP, Arrow, Scene, Text, VGroup

from puzzle import Line


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
