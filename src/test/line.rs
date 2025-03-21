use crate::game::{Game, SegmentPlacement, Square};

fn line_from_str(line_str: &str) -> Vec<Square> {
    line_str
        .chars()
        .map(|c| match c {
            '_' => Square::Unknown,
            'x' => Square::Empty,
            'o' => Square::Filled,
            _ => panic!("ruh roh"),
        })
        .collect()
}

pub fn str_from_placements(placements: Option<Vec<SegmentPlacement>>) -> Option<String> {
    placements.map(|placements| {
        placements
            .iter()
            .map(|placement| match placement {
                None => '_',
                Some(c) => format!("{:x}", *c).chars().next().unwrap(), // pls dont have more than 15 segs
            })
            .collect()
    })
}

pub fn test_line(hint: &[u32], line: &str, expected_line: Option<&str>) {
    assert_eq!(
        str_from_placements(Game::place_all_left(hint, &line_from_str(line))),
        expected_line.map(|s| s.to_owned())
    )
}

macro_rules! left_line_tests {
    ($($name:ident: $input:expr,)*) => {
    $(
        #[test]
        pub fn $name() {
            let (hint, line, expected) = $input;
            assert_eq!(
                str_from_placements(Game::place_all_left(hint, &line_from_str(line))),
                expected.map(|s| s.to_owned())
            )
        }
    )*
    }
}

macro_rules! right_line_tests {
    ($($name:ident: $input:expr,)*) => {
    $(
        #[test]
        pub fn $name() {
            let (hint, line, expected) = $input;
            assert_eq!(
                str_from_placements(Game::place_all_right(hint, &line_from_str(line))),
                expected.map(|s| s.to_owned())
            )
        }
    )*
    }
}

fn str_from_line(line: Vec<Square>) -> String {
    line.iter()
        .map(|s| match s {
            Square::Unknown => '_',
            Square::Empty => 'x',
            Square::Filled => 'o',
        })
        .collect()
}

macro_rules! overlap_tests {
    ($($name:ident: $input:expr,)*) => {
    $(
        #[test]
        pub fn $name() {
            let (hint, line, expected) = $input;
            assert_eq!(
                str_from_line(Game::relax_line(&line_from_str(line), hint).0),
                expected,
            )
        }
    )*
    }
}

left_line_tests! {
    left_one_seg_1: (&[3], "_____", Some("000__")),
    left_one_seg_2: (&[3], "___o_", Some("_000_")),
    left_one_seg_3: (&[3], "____o", Some("__000")),
    left_one_seg_4: (&[3], "x____", Some("_000_")),
    left_one_seg_5: (&[3], "xx___", Some("__000")),
    left_one_seg_6: (&[3], "x___x", Some("_000_")),
    left_two_seg_1: (&[3, 2], "__________", Some("000_11____")),
    left_two_seg_2: (&[3, 2], "____x_____", Some("000__11___")),
    left_two_seg_3: (&[3, 2], "_________o", Some("000_____11")),
    left_too_long_1: (&[3], "__", None::<&str>),
}

right_line_tests! {
    right_one_seg_1: (&[3], "_____", Some("__000")),
    // right_one_seg_2: (&[3], "___o_", Some("_000_")),
    // right_one_seg_3: (&[3], "____o", Some("__000")),
    // right_one_seg_4: (&[3], "x____", Some("_000_")),
    // right_one_seg_5: (&[3], "xx___", Some("__000")),
    // right_one_seg_6: (&[3], "x___x", Some("_000_")),
    right_two_seg_1: (&[3, 2], "__________", Some("____000_11")),
    // right_two_seg_2: (&[3, 2], "____x_____", Some("000__11___")),
    // right_two_seg_3: (&[3, 2], "_________o", Some("000_____11")),
    // right_too_long_1: (&[3], "__", None::<&str>),
}

overlap_tests! {
    overlap_1: (&[4], "______", "__oo__"),
    overlap_2: (&[4], "oooo__", "ooooxx"),
}
