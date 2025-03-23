use std::{
    fs::File,
    io::{self, Write},
    time::Duration,
    vec,
};

use crossterm::{
    cursor::{self, MoveToNextLine},
    execute, queue,
    style::{self, Print, Stylize},
    terminal,
};
use game::{Game, Square};

mod game;
mod render;
mod test;
use crate::test::line::test_line;

fn main() -> anyhow::Result<()> {
    // let col_hints = vec![
    //     vec![4],
    //     vec![2, 1],
    //     vec![1, 3, 1],
    //     vec![8],
    //     vec![7],
    //     vec![6],
    //     vec![4],
    // ];
    //
    // let row_hints = vec![
    //     vec![5],
    //     vec![2, 4],
    //     vec![1, 5],
    //     vec![1, 5],
    //     vec![1, 5],
    //     vec![1, 3],
    //     vec![3],
    //     vec![1],
    // ];
    let col_hints = vec![
        vec![1, 3],
        vec![1, 5, 1],
        vec![5, 3],
        vec![2, 1, 1],
        vec![4],
        vec![2],
        vec![2],
        vec![1, 1],
        vec![1, 1, 1],
        vec![1, 1, 1, 1],
    ];

    let row_hints = vec![
        vec![2],
        vec![1, 1],
        vec![2],
        vec![3, 1],
        vec![4, 1],
        vec![2, 2, 1, 1],
        vec![2, 3, 1],
        vec![6, 1],
        vec![1, 1, 1],
        vec![1, 1, 1],
    ];
    let mut file = File::create("solution.txt")?;
    file.write_all(
        row_hints
            .clone()
            .iter()
            .map(|hint| {
                hint.iter()
                    .map(|seg| seg.to_string())
                    .collect::<Vec<_>>()
                    .join(" ")
            })
            .collect::<Vec<_>>()
            .join("\n")
            .as_bytes(),
    )?;
    file.write(b"\n\n");
    file.write_all(
        col_hints
            .clone()
            .iter()
            .map(|hint| {
                hint.iter()
                    .map(|seg| seg.to_string())
                    .collect::<Vec<_>>()
                    .join(" ")
            })
            .collect::<Vec<_>>()
            .join("\n")
            .as_bytes(),
    )?;
    file.write(b"\n\n");
    let mut test_game = game::Game::new(col_hints, row_hints)?;
    let mut solver = game::Solver::new(test_game);

    solver.solve(&mut Some(&mut file));

    let mut stdout = io::stdout();
    let _ = execute!(
        stdout,
        terminal::EnterAlternateScreen,
        cursor::MoveTo(0, 0),
        Print(render::double_vec_to_string(solver.game.render_all()))
    )?;

    std::thread::sleep(Duration::from_secs(1));
    execute!(stdout, terminal::LeaveAlternateScreen)?;
    Ok(())
}
