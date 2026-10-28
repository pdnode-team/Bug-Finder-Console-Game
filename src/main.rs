mod engine;

use crossterm::{
    event::{self, Event, KeyCode},
    execute,
    terminal::{EnterAlternateScreen, LeaveAlternateScreen, disable_raw_mode, enable_raw_mode},
};
use engine::{Map, Npc, Player};
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

    let map = Map::from_strings(&[
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
    ]);

    let mut npcs = vec![Npc::new(
        'H',
        12,
        5,
        vec![
            "Hello!",
            "Welcome to ██████",
            "This place is very old and fragile",
            "If you want to escape...",
            "You can look for bugs and reduce \"system stability\"",
            "Remember, the lower the system stability, the greater the danger you're in",
            "Oh no",
            "NOOOOOOOO",
            "███ is coming!",
            "Don't get caught by ███!",
            "Hurry to that door!!!",
            ".............",
        ],
    )];

    let mut player = Player { x: 2, y: 2 };
    let mut talking_to: Option<usize> = None;

    let mut last_move = Instant::now();
    let mut last_action = Instant::now();
    let move_cooldown = Duration::from_millis(180);
    let action_cooldown = Duration::from_millis(200);

    loop {
        terminal.draw(|frame| {
            let area = frame.area();

            let display = map.render(&player, &npcs);
            let map_paragraph = Paragraph::new(display)
                .block(
                    Block::default()
                        .title("BugFinder | WASD(Move)  E(Talk)  Space(Continue)  q(Exit)")
                        .borders(Borders::ALL),
                )
                .style(Style::default().fg(Color::White));

            let chunks = Layout::default()
                .direction(Direction::Vertical)
                .constraints([Constraint::Min(5), Constraint::Length(5)])
                .split(area);

            frame.render_widget(map_paragraph, chunks[0]);

            if let Some(idx) = talking_to {
                frame.render_widget(Clear, chunks[1]);
                let dialog = Paragraph::new(npcs[idx].current_line())
                    .block(
                        Block::default()
                            .title("Talk")
                            .borders(Borders::ALL)
                            .style(Style::default().fg(Color::Yellow)),
                    )
                    .wrap(Wrap { trim: true });
                frame.render_widget(dialog, chunks[1]);
            } else {
                let near = npcs.iter().any(|n| n.is_adjacent(player.x, player.y));
                let hint = if near {
                    "Press E to Talk"
                } else {
                    "Talk with NPC"
                };
                let hint_widget = Paragraph::new(hint)
                    .block(Block::default().borders(Borders::ALL).title("Tips"))
                    .style(Style::default().fg(Color::DarkGray));
                frame.render_widget(hint_widget, chunks[1]);
            }
        })?;

        if event::poll(Duration::from_millis(50))? {
            if let Event::Key(key) = event::read()? {
                let can_move = last_move.elapsed() >= move_cooldown;
                let can_action = last_action.elapsed() >= action_cooldown;

                match key.code {
                    KeyCode::Char('q') => break,

                    KeyCode::Char('e') | KeyCode::Char('E')
                        if can_action && talking_to.is_none() =>
                    {
                        if let Some(idx) =
                            npcs.iter().position(|n| n.is_adjacent(player.x, player.y))
                        {
                            talking_to = Some(idx);
                            npcs[idx].reset();
                            last_action = Instant::now();
                        }
                    }

                    KeyCode::Char(' ') | KeyCode::Esc if can_action => {
                        if let Some(idx) = talking_to {
                            if !npcs[idx].advance() {
                                talking_to = None;
                            }
                            last_action = Instant::now();
                        }
                    }

                    KeyCode::Char('w') | KeyCode::Up if can_move && talking_to.is_none() => {
                        if player.try_move(0, -1, &map) {
                            last_move = Instant::now();
                        }
                        while event::poll(Duration::from_millis(0))? {
                            let _ = event::read();
                        }
                    }
                    KeyCode::Char('s') | KeyCode::Down if can_move && talking_to.is_none() => {
                        if player.try_move(0, 1, &map) {
                            last_move = Instant::now();
                        }
                        while event::poll(Duration::from_millis(0))? {
                            let _ = event::read();
                        }
                    }
                    KeyCode::Char('a') | KeyCode::Left if can_move && talking_to.is_none() => {
                        if player.try_move(-1, 0, &map) {
                            last_move = Instant::now();
                        }
                        while event::poll(Duration::from_millis(0))? {
                            let _ = event::read();
                        }
                    }
                    KeyCode::Char('d') | KeyCode::Right if can_move && talking_to.is_none() => {
                        if player.try_move(1, 0, &map) {
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
