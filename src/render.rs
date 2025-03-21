use std::fmt::Display;

use anyhow::Result;
use crossterm::style::Stylize;

use crate::game::{Game, Hint, Square};

impl Display for Square {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Square::Unknown => write!(f, "{}", " ".on_white()),
            Square::Filled => write!(f, "{}", "■".black().on_white()),
            Square::Empty => write!(f, "{}", "X".black().on_white()),
        }
    }
}

/*
* object: 123
*         456
* buffer: abcdef
*         ghijkl
*         mnopqr
* row: 1
* col: 1
* output: abcdef
*         g123kl
*         m456qr
*/
pub fn place_object<T: Clone>(
    object: Vec<Vec<T>>,
    row: usize,
    col: usize,
    buffer: &mut [Vec<T>],
) -> Result<()> {
    let obj_cols = object[0].len();
    for (i, obj_row) in object.iter().enumerate() {
        buffer[i + row].splice(col..col + obj_cols, obj_row.to_vec());
    }
    Ok(())
}

pub fn double_vec_to_string<T: Display>(buffer: Vec<Vec<T>>) -> String {
    buffer
        .into_iter()
        .map(|inner| inner.into_iter().map(|x| x.to_string()).collect::<String>())
        .collect::<Vec<_>>()
        .join("\n")
}

impl Game {
    pub fn render_hints(hints: &[Hint]) -> Vec<Vec<String>> {
        // im just gonna overly abstract this logic bc "readability" or whatever tf that is
        fn render_hint(hint: &Hint, max_segments: usize, max_digits: usize) -> Vec<String> {
            let segments = hint.len();
            let mut dark_grey = false;
            let mut padded_hint: Vec<Option<u32>> = Vec::with_capacity(max_segments);
            // hint_vec.extend(vec![None; max_segments - segments]);
            // womp womp thats an unecessary heap allocation so im doing this shit instead
            for _ in 0..max_segments - segments {
                padded_hint.push(None);
            }
            padded_hint.extend(hint.iter().map(|segment| Some(*segment)));
            let mut styled_hint_chars: Vec<String> = Vec::with_capacity(max_segments * max_digits); // The string stored in this vec is the chars in each segment. they are all len(max_digits)
            for segment in padded_hint {
                let mut padded_segment_chars: String = String::with_capacity(max_digits);
                let segment_str = match segment {
                    Some(s) => s.to_string(),
                    None => "".to_string(),
                };
                // ya nvm idc, allocate deez nuts
                padded_segment_chars.extend(vec![" "; max_digits - segment_str.len()]);
                padded_segment_chars.push_str(&segment_str);

                for character in padded_segment_chars.chars() {
                    match dark_grey {
                        true => {
                            styled_hint_chars.push(character.black().on_dark_grey().to_string())
                        }
                        false => styled_hint_chars.push(character.black().on_grey().to_string()),
                    }
                }
                dark_grey = !dark_grey;
            }
            styled_hint_chars
        }

        let max_digits = hints
            .iter()
            .flatten()
            .map(|segment| segment.to_string().len())
            .max()
            .unwrap();

        let max_segments = hints.iter().map(|hint| hint.len()).max().unwrap();

        hints
            .iter()
            .map(|hint| render_hint(hint, max_segments, max_digits))
            .collect()
    }

    pub fn render_grid(&self) -> Vec<Vec<String>> {
        self.grid
            .iter()
            .map(|row| row.iter().map(|cell| format!("{}", cell)).collect())
            .collect()
    }

    pub fn render_all(&mut self) -> Vec<Vec<String>> {
        #[inline]
        fn transpose(matrix: Vec<Vec<String>>) -> Vec<Vec<String>> {
            let mut transposed = vec![vec!["".to_string(); matrix.len()]; matrix[0].len()];
            for i in 0..matrix.len() {
                for j in 0..matrix[0].len() {
                    transposed[j][i].clone_from(&matrix[i][j]);
                }
            }
            transposed
        }

        let rendered_row_hints = Self::render_hints(&self.row_hints);
        let rendered_col_hints = transpose(Self::render_hints(&self.col_hints));

        let col_hints_pos = (0usize, rendered_row_hints[0].len()); // Places top bar of hints just to
                                                                   // the right of where the side bar ends laterally
        let row_hints_pos = (rendered_col_hints.len(), 0usize); // Places side bar just below where the
                                                                // top bar ends vertically

        let size = (
            rendered_col_hints.len() + rendered_row_hints.len(),
            rendered_col_hints[0].len() + rendered_row_hints[0].len(),
        );

        let mut rendered_game = vec![vec![" ".to_string(); size.1]; size.0];
        place_object(
            rendered_col_hints,
            col_hints_pos.0,
            col_hints_pos.1,
            &mut rendered_game,
        )
        .unwrap();

        place_object(
            rendered_row_hints,
            row_hints_pos.0,
            row_hints_pos.1,
            &mut rendered_game,
        )
        .unwrap();

        self.grid_pos = Some((row_hints_pos.0, col_hints_pos.1));
        place_object(
            self.render_grid(),
            self.grid_pos.unwrap().0,
            self.grid_pos.unwrap().1,
            &mut rendered_game,
        )
        .unwrap();

        rendered_game
    }
}
