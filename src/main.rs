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

// Yepp!
#[derive(Clone, Copy)]
enum TalkPhase {
    Lines,
    Choosing,
    Reply(usize),
}

fn main() -> io::Result<()> {
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    let mut map = Map::from_strings(&[
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

    let mut npcs = vec![
        Npc::new(
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
        )
        .with_choices(vec![
            ("Who is ███?", "What ███?"),
            ("Why I'm here?", "JUST GO! Otherwise, it’ll be too late!"),
        ]),
    ];

    let mut player = Player { x: 2, y: 2 };
    let mut talking_to: Option<usize> = None;
    let mut talk_phase = TalkPhase::Lines;

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
                .constraints([Constraint::Min(5), Constraint::Length(8)])
                .split(area);

            frame.render_widget(map_paragraph, chunks[0]);

            if let Some(idx) = talking_to {
                frame.render_widget(Clear, chunks[1]);

                let text = match talk_phase {
                    TalkPhase::Lines => npcs[idx].current_line().to_string(),
                    TalkPhase::Choosing => {
                        let mut text = String::from("Choose:\n");
                        for (i, choice) in npcs[idx].choices.iter().enumerate() {
                            text.push_str(&format!("{}. {}\n", i + 1, choice.label));
                        }
                        text
                    }
                    TalkPhase::Reply(pick) => npcs[idx]
                        .choices
                        .get(pick)
                        .map(|choice| choice.reply.clone())
                        .unwrap_or_default(),
                };

                let dialog = Paragraph::new(text)
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
            let event = event::read()?;
            if let Event::Key(key) = event {
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
                            talk_phase = TalkPhase::Lines;
                            last_action = Instant::now();
                        }
                    }

                    KeyCode::Char(' ') if can_action => {
                        if let Some(idx) = talking_to {
                            match talk_phase {
                                TalkPhase::Lines => {
                                    if !npcs[idx].advance() {
                                        if npcs[idx].choices.is_empty() {
                                            talking_to = None;
                                            npcs[idx].talked = true;
                                        } else {
                                            talk_phase = TalkPhase::Choosing;
                                        }
                                    }
                                }
                                TalkPhase::Reply(_) => {
                                    talking_to = None;
                                    talk_phase = TalkPhase::Lines;
                                    npcs[idx].talked = true;
                                }
                                TalkPhase::Choosing => {}
                            }
                            last_action = Instant::now();
                        }
                    }

                    KeyCode::Esc if can_action && talking_to.is_some() => {
                        talking_to = None;
                        talk_phase = TalkPhase::Lines;
                        last_action = Instant::now();
                    }

                    KeyCode::Char('1') | KeyCode::Char('2') if can_action => {
                        if let (Some(idx), TalkPhase::Choosing) = (talking_to, talk_phase) {
                            let pick = match key.code {
                                KeyCode::Char('1') => 0,
                                _ => 1,
                            };
                            if pick < npcs[idx].choices.len() {
                                talk_phase = TalkPhase::Reply(pick);
                                last_action = Instant::now();
                            }
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

        if npcs[0].talked {
            map.set_tile(12, 5, '.')
        }
    }

    disable_raw_mode()?;
    execute!(terminal.backend_mut(), LeaveAlternateScreen)?;
    terminal.show_cursor()?;

    Ok(())
}
