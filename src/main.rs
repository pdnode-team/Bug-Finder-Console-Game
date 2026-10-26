use crossterm::{
    event::{self, Event, KeyCode},
    execute,
    terminal::{EnterAlternateScreen, LeaveAlternateScreen, disable_raw_mode, enable_raw_mode},
};
use ratatui::{
    Terminal,
    backend::CrosstermBackend,
    style::{Color, Style},
    widgets::{Block, Borders, Paragraph},
};
use std::io;
use std::time::{Duration, Instant};

fn main() -> io::Result<()> {
    // 初始化终端
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    // 玩家位置
    let mut player_x = 2;
    let mut player_y = 2;

    // 移动冷却：上次移动的时间 + 冷却间隔
    let mut last_move = Instant::now();
    let move_cooldown = Duration::from_millis(150); // 150毫秒才能再移动一次（可调整）

    // 固定地图
    let map = vec![
        "####################",
        "#..................#",
        "#..................#",
        "#..................#",
        "#..................#",
        "#..................#",
        "#..................#",
        "#..................#",
        "#..................#",
        "####################",
    ];

    loop {
        // 画画面
        terminal.draw(|frame| {
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

            let paragraph = Paragraph::new(display)
                .block(
                    Block::default()
                        .title("ASCII地图游戏 | WASD移动 q退出")
                        .borders(Borders::ALL),
                )
                .style(Style::default().fg(Color::White));

            frame.render_widget(paragraph, frame.area());
        })?;

        // 处理按键（非阻塞）
        if event::poll(Duration::from_millis(50))? {
            if let Event::Key(key) = event::read()? {
                // 只有冷却结束了才允许移动
                let can_move = last_move.elapsed() >= move_cooldown;

                match key.code {
                    KeyCode::Char('q') => break,

                    KeyCode::Char('w') | KeyCode::Up if can_move => {
                        if player_y > 1 {
                            player_y -= 1;
                            last_move = Instant::now();
                        }
                    }
                    KeyCode::Char('s') | KeyCode::Down if can_move => {
                        if player_y < map.len() - 2 {
                            player_y += 1;
                            last_move = Instant::now();
                        }
                    }
                    KeyCode::Char('a') | KeyCode::Left if can_move => {
                        if player_x > 1 {
                            player_x -= 1;
                            last_move = Instant::now();
                        }
                    }
                    KeyCode::Char('d') | KeyCode::Right if can_move => {
                        if player_x < map[0].len() - 2 {
                            player_x += 1;
                            last_move = Instant::now();
                        }
                    }
                    _ => {}
                }
            }
        }
    }

    // 退出清理
    disable_raw_mode()?;
    execute!(terminal.backend_mut(), LeaveAlternateScreen)?;
    terminal.show_cursor()?;

    Ok(())
}
