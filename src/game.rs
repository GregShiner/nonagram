use core::panic;
use std::{collections::BinaryHeap, fmt::Display, fs::File, io::Write, iter::zip, usize};

use anyhow::Result;

pub type Hint = Vec<u32>;
/// Given a hint and a line with some of the segments placed, a line of SegmentPlacements may look
/// like this:
/// Given:
/// Hint: 2, 3, 2
/// Line length: 10
/// Line:           OOXXOOOXOO (O: filled space, X: empty space)
/// SegPlacements:  00NN111N22
/// N Represents a None, and each number represents a Some(usize) where the number is the index of
/// the Hints that is at that possition
pub type SegmentPlacement = Option<usize>;

#[derive(Clone, PartialEq, Eq)]
pub enum Square {
    Unknown,
    Filled,
    Empty,
}

pub struct Game {
    pub rows: usize,
    pub cols: usize,
    pub col_hints: Vec<Hint>,
    pub row_hints: Vec<Hint>,
    pub grid_pos: Option<(usize, usize)>, // Calculated when render_all is called
    pub grid: Vec<Vec<Square>>,
}

pub enum Job {
    Row(usize),
    Col(usize),
}

pub struct Solver {
    pub game: Game,
    // pub job_list: BinaryHeap<(i32, Job)>,
    pub solved_rows: Vec<bool>,
    pub solved_cols: Vec<bool>,
}

impl Game {
    pub fn new(col_hints: Vec<Hint>, row_hints: Vec<Hint>) -> Result<Game> {
        let cols = col_hints.len();
        let rows = row_hints.len();

        Ok(Game {
            rows,
            cols,
            col_hints,
            row_hints,
            grid_pos: None,
            grid: vec![vec![Square::Unknown; cols]; rows],
        })
    }

    /// Gets a row as a line and its corresponding hint
    pub fn get_row(&self, i: usize) -> (Hint, Vec<Square>) {
        (self.row_hints[i].clone(), self.grid[i].clone())
    }

    pub fn set_row(&mut self, i: usize, row: Vec<Square>) {
        self.grid[i] = row;
    }

    /// Gets a column as a line and its corresponding hint
    pub fn get_col(&self, i: usize) -> (Hint, Vec<Square>) {
        (
            self.col_hints[i].clone(),
            self.grid.iter().map(|row| row[i].clone()).collect(),
        )
    }

    pub fn set_col(&mut self, i: usize, col: Vec<Square>) {
        self.grid
            .iter_mut()
            .zip(col.iter())
            .for_each(|(old, new)| old[i] = new.clone())
    }

    /// Checks if a line meets the criteria of a corresponding hint
    pub fn check_line(hint: &[u32], line: &[Square]) -> bool {
        // theres a lot of cases so heres some important ones
        // last segment is at the end of the line
        // last segment is not at the end of the line
        //      there may or may not be more filled cells after it
        // TODO: Maybe see if i can save a heap allocation here
        // Its probably possible by comparing the input hint to the line
        // I can prob at least do smth like clone hint, then instead of creating a new vec and
        // pushing to it, just subtract segments from the new hint. This would guarantee only 1
        // heap allocation and would allow for short circuits in some false cases.
        let mut segments: Hint = Vec::new(); // maybe a capacity here would be more efficient
        let mut curr_segment_len = 0u32; // This gets set to 0 when not in a segment (ya sure an
                                         // enum could encode whether it's in a segment or not, idc tho)

        for square in line {
            match square {
                Square::Filled => {
                    curr_segment_len += 1;
                }
                _ => {
                    if curr_segment_len != 0 {
                        segments.push(curr_segment_len);
                    }
                    curr_segment_len = 0
                }
            }
        }

        if curr_segment_len != 0 {
            segments.push(curr_segment_len);
        }

        segments == hint
    }

    /// Given the current state of a line and its hint, return a vec of the segments placed as far
    /// left as possible. The values represent the index in the Hint vec that they correspond to
    pub fn place_all_left(hint: &[u32], line: &[Square]) -> Option<Vec<SegmentPlacement>> {
        /// Check if a segment fits starting at start_index
        /// Does not check if it touches other filled spaces
        /// Only checks if there are x's in the way
        fn can_seg_be_placed(segment: u32, line: &[Square], start_index: usize) -> bool {
            // First check that the segment will fit within the bounds of the line
            let segment = segment as usize; // segment gets used a lot with start_loc to index
                                            // line, so we shadow it with this conversion to usize
            if segment > line.len() {
                return false;
            }

            if line[start_index..start_index + segment] // TODO: Check if this needs + 1 (prob no)
                .iter()
                .any(|square| *square == Square::Empty)
            {
                return false;
            }
            true
        }

        /// Places a segment as far left as possible. Returns the index of the left-most index the
        /// segment can start at if it can be placed, else None
        /// Takes an index to start the search at
        fn place_segment_left(
            segment: u32,
            line: &[Square],
            search_start_index: usize,
        ) -> Option<usize> {
            // Loop through every possible starting pos, which starts at start_index and goes up to
            // 1 segment length before the end of the line since it can't fit anywhere after that.
            (search_start_index..line.len() + 1 - segment as usize)
                .find(|i| can_seg_be_placed(segment, line, *i))
        }

        fn place_segment(segment: u32, line: &mut [Square], index: usize) {
            line[index..index + segment as usize]
                .iter_mut()
                .for_each(|square| *square = Square::Filled);
        }

        fn place_in_segment_placements(
            // Segment placements is a representation of the Line that includes data of what
            // segment a cell is a part of
            placements: &mut [SegmentPlacement],
            segment: u32,
            segment_index: usize,
            pos: usize,
        ) {
            placements[pos..pos + segment as usize]
                .iter_mut()
                .for_each(|cell| *cell = Some(segment_index));
        }

        /// Given a slice of line indexes for each hint, place them on the line
        fn place_segment_positions(
            positions: &[usize],
            hint: &[u32],
            size: usize,
        ) -> Vec<SegmentPlacement> {
            let mut segment_placements: Vec<SegmentPlacement> = vec![None; size];
            assert_eq!(positions.len(), hint.len());
            for (pos, (seg_index, seg)) in zip(positions, hint.iter().enumerate()) {
                place_in_segment_placements(&mut segment_placements, *seg, seg_index, *pos)
            }
            segment_placements
        }

        /// Recursively places each segment on the line.
        /// On each recursive step, places the first segment in the slice as far left as possible
        /// starting at the start_index
        /// Returns an accumulating line of positions for each segment to be placed at
        fn rec_place_left(
            hint: &[u32],
            hint_index: usize,
            line: &[Square],
            start_index: usize,
        ) -> Option<Vec<usize>> {
            let seg_to_place = match hint.get(hint_index) {
                None => {
                    // BASE CASE
                    // Reached end of segments, check if line is valid.
                    return match Game::check_line(hint, line) {
                        // The line is valid and theres no more segs to place
                        true => Some(vec![]),
                        false => None,
                    };
                }
                Some(seg) => seg,
            };

            // This may be able to be optimized to be O(n) instead of O(n^2) by making x
            // checking and validity checking happen in the same loop
            for i in start_index..line.len() + 1 - *seg_to_place as usize {
                // TODO: Check for off by 1
                let placement_index = match place_segment_left(*seg_to_place, line, i) {
                    None => {
                        return None;
                    }
                    Some(placement_index) => placement_index,
                };
                let mut new_line: Vec<_> = line.to_vec(); // ya we just heap allocating it all
                place_segment(*seg_to_place, &mut new_line, placement_index);
                let next_partial = match rec_place_left(
                    hint,
                    hint_index + 1,
                    &new_line,
                    placement_index + *seg_to_place as usize + 1, // TODO: No fuckin way this is correct (Update, I was right, this comment is being left bc its funny)
                ) {
                    None => continue,
                    Some(partial_line) => partial_line,
                };
                // Putting this before next_partial may or may not improve performance.
                // Having it after make a heap alloc only happen when theres a valid next_partial
                // But having it before may allow me to not build backwards
                let mut new_partial = Vec::with_capacity(next_partial.len());
                new_partial.push(placement_index);
                new_partial.extend(next_partial);
                return Some(new_partial); // TODO: PLEASE find any way to not build a vector BACKWARDS,
                                          // realloc is gonna go nuts
            }
            None
        }
        let positions = rec_place_left(hint, 0, line, 0);
        positions.map(|positions| place_segment_positions(&positions, hint, line.len()))
    }

    pub fn place_all_right(hint: &[u32], line: &[Square]) -> Option<Vec<SegmentPlacement>> {
        let mut reverse_line = line.to_vec();
        reverse_line.reverse();
        let mut reverse_hint = hint.to_vec();
        reverse_hint.reverse();

        let mut placements = Game::place_all_left(&reverse_hint, &reverse_line);
        if let Some(placements) = placements.as_mut() {
            placements.reverse();
        }
        // Since the hint is reversed, we have to flip all of the indexes back
        if let Some(placements) = placements.as_mut() {
            placements
                .iter_mut()
                .for_each(|p| *p = p.map(|p| hint.len() - p - 1))
        }
        placements
    }

    pub fn refine_line(line: &[Square], hint: &[u32]) -> (Vec<Square>, bool, bool) {
        let left_sol = Game::place_all_left(hint, line).expect("No left solution found");
        let right_sol = Game::place_all_right(hint, line).expect("No right solution found");

        // let mut new_line = vec![Square::Unknown; line.len()]; // Might be interesting for later
        // to try just cloning the original
        let mut new_line = line.to_vec();

        // General logic for this fucky ass algorithm
        // If the left sol and right sol have the same segment overlapping, then their overlap
        // must be a square.
        // If the gaps between the same 2 segments are overlapping, then their overlap must be
        // empty.

        // These track what the next segment will be to track what gap it is in.
        // This could prob be an enum thats None when in a segment, but this works too as long as
        // we check for squares first
        // Represents the value of the next segment when in an
        // empty span.
        // EX: Placements: __00_111___22__
        //       next seg: 000011112222233;
        let mut solved = true;
        let mut changed = false;
        let mut left_sol_next_seg = 0;
        // Ditto for right sol
        let mut right_sol_next_seg = 0;
        for i in 0..line.len() {
            // If passing a segment, increment the next seg indicator
            if i > 0 && left_sol[i - 1].is_some() && left_sol[i].is_none() {
                left_sol_next_seg += 1;
            }

            if i > 0 && right_sol[i - 1].is_some() && right_sol[i].is_none() {
                right_sol_next_seg += 1;
            }

            // If they are equal and Some, there is an overlap
            if left_sol[i].is_some() && (left_sol[i] == right_sol[i]) {
                if new_line[i] != Square::Filled {
                    changed = true;
                }
                new_line[i] = Square::Filled;
            }
            // If both are in a gap and they are preceding the same next segment, its empty
            else if left_sol[i].is_none()
                && right_sol[i].is_none()
                && (left_sol_next_seg == right_sol_next_seg)
            {
                if new_line[i] != Square::Empty {
                    changed = true;
                }
                new_line[i] = Square::Empty;
            } else {
                solved = false;
            }
        }
        (new_line, solved, changed)
    }
}

impl Solver {
    pub fn new(game: Game) -> Self {
        let rows = game.rows;
        let cols = game.cols;
        Solver {
            game,
            solved_rows: vec![false; rows],
            solved_cols: vec![false; cols],
        }
    }

    pub fn solve(&mut self, file: &mut Option<&mut File>) {
        loop {
            let mut puzzle_changed = false;
            for i in 0..self.game.rows {
                if self.solved_rows[i] {
                    continue;
                }

                let (hint, line) = self.game.get_row(i);
                let (new_row, solved, line_changed) = Game::refine_line(&line, &hint);
                self.solved_rows[i] = solved;
                puzzle_changed |= line_changed;
                if !line_changed {
                    continue;
                }
                if let Some(f) = file.as_mut() {
                    f.write_all(i.to_string().as_bytes()).unwrap();
                    f.write_all(b" row ").unwrap();
                    f.write_all(
                        new_row
                            .iter()
                            .map(|square| match square {
                                Square::Unknown => "_",
                                Square::Filled => "o",
                                Square::Empty => "x",
                            })
                            .collect::<Vec<_>>()
                            .join(" ")
                            .as_bytes(),
                    )
                    .unwrap();
                    f.write_all(b"\n").unwrap();
                };
                self.game.set_row(i, new_row);
            }

            for i in 0..self.game.cols {
                if self.solved_cols[i] {
                    continue;
                }

                let (hint, line) = self.game.get_col(i);
                let (new_col, solved, line_changed) = Game::refine_line(&line, &hint);
                self.solved_cols[i] = solved;
                puzzle_changed |= line_changed;
                if !line_changed {
                    continue;
                }
                if let Some(f) = file.as_mut() {
                    f.write_all(i.to_string().as_bytes()).unwrap();
                    f.write_all(b" col ").unwrap();
                    f.write_all(
                        new_col
                            .iter()
                            .map(|square| match square {
                                Square::Unknown => "_",
                                Square::Filled => "o",
                                Square::Empty => "x",
                            })
                            .collect::<Vec<_>>()
                            .join(" ")
                            .as_bytes(),
                    )
                    .unwrap();
                    f.write_all(b"\n").unwrap();
                };
                self.game.set_col(i, new_col);
            }

            // Check if all rows and cols are solved
            if self.solved_rows.iter().all(|val| *val) && self.solved_cols.iter().all(|val| *val) {
                break;
            }
            if !puzzle_changed {
                panic!("Can't be solved completely");
            }
        }
    }
}

impl Display for Game {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let cols = self.cols;
        let rows = self.rows;
        let max_col_hints = self.col_hints.iter().map(|hint| hint.len()).max().unwrap();
        let max_row_hints = self.row_hints.iter().map(|hint| hint.len()).max().unwrap();
        let mut buffer = vec![vec![" "; cols + max_row_hints]; rows + max_col_hints];
        Ok(())
    }
}
