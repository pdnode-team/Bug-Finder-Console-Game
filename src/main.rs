use crossterm::{
    event::{self, Event, KeyCode},
    execute,
    terminal::{EnterAlternateScreen, LeaveAlternateScreen, disable_raw_mode, enable_raw_mode},
};
use ratatui::{
    Terminal,
    backend::CrosstermBackend,
    layout::{Constraint, Direction, Layout},
    style::{Color, Style},
    widgets::{Block, Borders, Clear, Paragraph, Wrap},
};
use std::io;
use std::time::{Duration, Instant};

fn main() -> io::Result<()> {
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    let mut player_x = 2;
    let mut player_y = 2;
    let npc_x = 12;
    let npc_y = 5;

    let mut show_dialog = false;
    let mut last_move = Instant::now();
    let mut last_action = Instant::now();
    let move_cooldown = Duration::from_millis(180);
    let action_cooldown = Duration::from_millis(200);

    let map = vec![
        "####################",
        "#..................#",
        "#..................#",
        "#..................#",
        "#..................#",
        "#...........H......#",
        "#..................#",
        "#..................#",
        "#..................#",
        "####################",
    ];

    loop {
        terminal.draw(|frame| {
            let area = frame.area();

            // Map
            let mut display = String::new();
            for (y, line) in map.iter().enumerate() {
                for (x, ch) in line.chars().enumerate() {
                    if x == player_x && y == player_y {
                        display.push('@');
                    } else {
                        display.push(ch);
                    }
                }
                display.push('\n');
            }

            let map_paragraph = Paragraph::new(display)
                .block(
                    Block::default()
                        .title("BugFinder | Press q to exit")
                        .borders(Borders::ALL),
                )
                .style(Style::default().fg(Color::White));

            let chunks = Layout::default()
                .direction(Direction::Vertical)
                .constraints([Constraint::Min(5), Constraint::Length(4)])
                .split(area);

            frame.render_widget(map_paragraph, chunks[0]);

            // Talk Window
            if show_dialog {
                frame.render_widget(Clear, chunks[1]);
                let dialog = Paragraph::new("Hello")
                    .block(
                        Block::default()
                            .title("Talk")
                            .borders(Borders::ALL)
                            .style(Style::default().fg(Color::Yellow)),
                    )
                    .wrap(Wrap { trim: true });
                frame.render_widget(dialog, chunks[1]);
            } else {
                // Tips & Talk
                let near_npc = {
                    let dx = (player_x as i32 - npc_x as i32).abs();
                    let dy = (player_y as i32 - npc_y as i32).abs();
                    dx <= 1 && dy <= 1 && !(dx == 0 && dy == 0)
                };

                let hint = if near_npc {
                    "Press E to talk"
                } else {
                    "Task: speak with the mysterious person."
                };

                let hint_widget = Paragraph::new(hint)
                    .block(Block::default().borders(Borders::ALL).title("Tips"))
                    .style(Style::default().fg(Color::DarkGray));
                frame.render_widget(hint_widget, chunks[1]);
            }
        })?;

        // Input
        if event::poll(Duration::from_millis(50))? {
            if let Event::Key(key) = event::read()? {
                let can_move = last_move.elapsed() >= move_cooldown;
                let can_action = last_action.elapsed() >= action_cooldown;

                match key.code {
                    KeyCode::Char('q') => break,

                    // Talk
                    KeyCode::Char('e') | KeyCode::Char('E') if can_action && !show_dialog => {
                        let dx = (player_x as i32 - npc_x as i32).abs();
                        let dy = (player_y as i32 - npc_y as i32).abs();
                        if dx <= 1 && dy <= 1 && !(dx == 0 && dy == 0) {
                            show_dialog = true;
                            last_action = Instant::now();
                        }
                    }

                    // Space
                    KeyCode::Char(' ') | KeyCode::Esc if show_dialog && can_action => {
                        show_dialog = false;
                        last_action = Instant::now();
                    }

                    // Move
                    KeyCode::Char('w') | KeyCode::Up if can_move && !show_dialog => {
                        if player_y > 1 {
                            player_y -= 1;
                            last_move = Instant::now();
                        }
                        while event::poll(Duration::from_millis(0))? {
                            let _ = event::read();
                        }
                    }
                    KeyCode::Char('s') | KeyCode::Down if can_move && !show_dialog => {
                        if player_y < map.len() - 2 {
                            player_y += 1;
                            last_move = Instant::now();
                        }
                        while event::poll(Duration::from_millis(0))? {
                            let _ = event::read();
                        }
                    }
                    KeyCode::Char('a') | KeyCode::Left if can_move && !show_dialog => {
                        if player_x > 1 {
                            player_x -= 1;
                            last_move = Instant::now();
                        }
                        while event::poll(Duration::from_millis(0))? {
                            let _ = event::read();
                        }
                    }
                    KeyCode::Char('d') | KeyCode::Right if can_move && !show_dialog => {
                        if player_x < map[0].len() - 2 {
                            player_x += 1;
                            last_move = Instant::now();
                        }
                        while event::poll(Duration::from_millis(0))? {
                            let _ = event::read();
                        }
                    }

                    _ => {}
                }
            }
        }
    }

    disable_raw_mode()?;
    execute!(terminal.backend_mut(), LeaveAlternateScreen)?;
    terminal.show_cursor()?;

    Ok(())
}
