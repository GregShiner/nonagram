use std::{
    error,
    fmt::{Debug, Display},
    path::Iter,
    usize,
};

use anyhow::Result;
use crossterm::{
    style::{Color, Stylize},
    terminal::size,
};
use thiserror::Error;

pub type Hint = Vec<u32>;

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

    /// Gets a column as a line and its corresponding hint
    pub fn get_col(&self, i: usize) -> (Hint, Vec<Square>) {
        (
            self.col_hints[i].clone(),
            self.grid.iter().map(|row| row[i].clone()).collect(),
        )
    }

    /// Checks if a line meets the criteria of a corresponding hint
    pub fn check_line(hint: Hint, line: Vec<Square>) -> bool {
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
        /* let mut in_segment = false; // TODO: maybe get rid of this
        let mut segment_len = 0u32;
        let mut hint_segment_index = 0usize;
        let mut hint_segment_len = hint[hint_segment_index];

        for square in line {
            match square {
                Square::Filled => {
                    in_segment = true;
                    segment_len += 1;
                }
                _ => {
                    in_segment = false;
                    if segment_len < hint_segment_len {
                        return false;
                    } else {
                        hint_segment_index += 1;
                        hint_segment_len = hint[hint_segment_index]; // This won't work when the
                                                                     // last segment is hit. the index will increment beyond where the hint ends
                    }
                    segment_len = 0;
                }
            }

            // if current segment is bigger than expected, it's no good
            if segment_len > hint_segment_len {
                return false;
            }
        }
        // check that all segments have been checked
        if hint_segment_index + 1 != hint.len() {
            return false;
        }
        // figure out what to do when the segment is at the end of the line
        if segment_len > 0 {}
        return true; */
    }

    /// Given the current state of a line and its hint, return a new line with squares either
    /// filled or crossed if they are guaranteed to be as such.
    // pub fn ease_line(hint: Hint, line: Vec<Square>) -> Vec<Square> {
    //     let mut new_line = line.clone();
    //     let mut placing_squares = false;
    //     let mut squares_remaining = 0u32;
    //     for (i, square) in line.iter().enumerate() {
    //         match square {
    //             Square::Unknown => todo!(),
    //             Square::Filled => todo!(),
    //             Square::Empty => todo!(),
    //         }
    //     }
    // }
    pub fn find_possible_indices(hint: Hint, line: Vec<Square>) -> Vec<Vec<usize>> {
        fn can_seg_be_placed(segment: u32, start_loc: usize, line: &Vec<Square>) -> bool {
            // First check that the segment will be placed within the bounds of the line
            let segment = segment as usize; // segment gets used a lot with start_loc to index
                                            // line, so we shadow it with this conversion to usize
            let end_loc = segment + start_loc - 1;
            if end_loc >= line.len() {
                return false;
            }
            // Now check that there are no x's where the segment is placed
            if line[start_loc..end_loc + 1] // Add back 1 since range ends are exclusive
                .iter()
                .any(|square| *square == Square::Empty)
            {
                return false;
            }
            // Finally, check that there are no filled squares on either side of the segment
            // using line.get returns None if its out of bounds, so this saves us the step of
            // bounds checking first, since we only care if its in bounds and has a square
            if line.get(start_loc - 1) == Some(Square::Filled).as_ref() {
                return false;
            }
            if line.get(start_loc + 1) == Some(Square::Filled).as_ref() {
                return false;
            }
            return true;
        }
        /// Places a segment as far left as possible. Returns the index of the left-most index the
        /// segment can start it if it can be placed, else None
        fn place_segment_left(
            segment: u32,
            min_index: usize,
            line: &mut Vec<Square>,
        ) -> Option<usize> {
            for i in min_index..line.len() - segment as usize + 1 {
                if can_seg_be_placed(segment, i, &line) {
                    return Some(i);
                }
            }
            return None;
        }
        let mut possible_positions: Vec<Vec<usize>> = Vec::with_capacity(hint.len());
        let mut next_segment_index = 0usize;
        let mut scratch_line = line.clone();
        // first, find initial valid position of all segments.
        // do this by placing each segment as far left as possible
        for segment in hint {
            let mut new_posibilities = Vec::new();
            match place_segment_left(segment, next_segment_index, &mut scratch_line) {
                Some(segment_index) => {
                    next_segment_index = segment_index + segment as usize + 1; // Add 1 because
                                                                               // there needs to be a gap of 1.
                    new_posibilities.push(segment_index);
                }
                None => todo!(),
            }
            possible_positions.push(new_posibilities);
        }
        possible_positions
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
