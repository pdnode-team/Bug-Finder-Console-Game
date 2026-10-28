use super::npc::Npc;
use super::player::Player;
use ratatui::style::Color;
use ratatui::text::{Line, Span, Text};
use std::collections::VecDeque;
use std::time::Duration;

/// One cell on the map.
///
/// `ch` is what the player sees. `color` is that character's foreground color.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Tile {
    pub ch: char,
    pub color: Color,
}

impl Tile {
    fn blank() -> Self {
        Self {
            ch: ' ',
            color: Color::White,
        }
    }
}

/// Something the map will do when [`Map::tick`] gives it time.
///
/// [`MapEvent::Pause`] is a wait. Nothing queued after it happens until the wait is over.
/// [`MapEvent::Set`] writes one colored character.
#[derive(Clone, Copy, Debug)]
pub enum MapEvent {
    Pause(Duration),
    Set {
        x: usize,
        y: usize,
        ch: char,
        color: Color,
    },
}

impl MapEvent {
    pub fn pause(ms: u64) -> Self {
        Self::Pause(Duration::from_millis(ms))
    }

    pub fn set(x: usize, y: usize, ch: char, color: Color) -> Self {
        Self::Set { x, y, ch, color }
    }
}

#[derive(Clone)]
enum Step {
    Pause(Duration),
    Paint(Vec<Paint>),
}

#[derive(Clone, Copy)]
struct Paint {
    x: usize,
    y: usize,
    ch: char,
    color: Color,
}

enum Ink {
    Auto,
    Fixed(Color),
}

enum Token {
    Char(char),
    Color(Color),
    Auto,
    Pause(Duration),
}

#[derive(Clone)]
pub struct Map {
    pub tiles: Vec<Vec<Tile>>,
    pub width: usize,
    pub height: usize,
    steps: VecDeque<Step>,
    pause_left: Duration,
}

impl Map {
    /// Build a map from text rows.
    ///
    /// Markup is not a tile. A color tag paints the rest of that line:
    /// `{red}` `{green}` `{yellow}` `{blue}` `{cyan}` `{magenta}` `{white}` `{gray}` `{darkgray}` `{black}`.
    /// Short forms: `{r}` `{g}` `{y}` `{b}` `{c}` `{m}` `{w}` `{a}` `{d}` `{k}`.
    /// `{auto}` returns to the normal colors (`#` is dark gray, everything else is white).
    /// `{p:400}` waits 400 milliseconds before the characters after it are written.
    /// The wait only advances when the game calls [`Map::tick`].
    pub fn from_strings(lines: &[&str]) -> Self {
        let events = events_from_lines(0, 0, lines);
        let height = lines.len();
        let width = events
            .iter()
            .filter_map(|event| match event {
                MapEvent::Set { x, .. } => Some(x + 1),
                MapEvent::Pause(_) => None,
            })
            .max()
            .unwrap_or(0);
        let mut map = Self {
            tiles: vec![vec![Tile::blank(); width]; height],
            width,
            height,
            steps: VecDeque::new(),
            pause_left: Duration::ZERO,
        };
        map.play(events);
        map
    }

    /// Queue `events`. Writes before the next pause happen immediately.
    /// Later writes wait, and [`Map::tick`] finishes them.
    pub fn play(&mut self, events: impl IntoIterator<Item = MapEvent>) {
        let mut batch = Vec::new();
        for event in events {
            match event {
                MapEvent::Pause(duration) => {
                    if !batch.is_empty() {
                        self.steps
                            .push_back(Step::Paint(std::mem::take(&mut batch)));
                    }
                    if !duration.is_zero() {
                        self.steps.push_back(Step::Pause(duration));
                    }
                }
                MapEvent::Set { x, y, ch, color } => batch.push(Paint { x, y, ch, color }),
            }
        }
        if !batch.is_empty() {
            self.steps.push_back(Step::Paint(batch));
        }
        self.drain_ready();
    }

    /// Same markup as [`Map::from_strings`], written at `(x, y)`.
    #[allow(dead_code)]
    pub fn play_lines(&mut self, x: usize, y: usize, lines: &[&str]) {
        self.play(events_from_lines(x, y, lines));
    }

    /// Move queued pauses and tile changes forward by `dt`.
    pub fn tick(&mut self, mut dt: Duration) {
        loop {
            if !self.pause_left.is_zero() {
                if dt < self.pause_left {
                    self.pause_left -= dt;
                    return;
                }
                dt -= self.pause_left;
                self.pause_left = Duration::ZERO;
            }

            match self.steps.pop_front() {
                Some(Step::Pause(duration)) => self.pause_left = duration,
                Some(Step::Paint(paints)) => self.apply(&paints),
                None => return,
            }
        }
    }

    /// `true` while a pause is running or a later tile change is still waiting.
    pub fn is_busy(&self) -> bool {
        !self.pause_left.is_zero() || !self.steps.is_empty()
    }

    pub fn is_walkable(&self, x: usize, y: usize) -> bool {
        if y >= self.height || x >= self.width {
            return false;
        }
        self.tiles[y][x].ch == '.'
    }

    pub fn render(&self, player: &Player, npcs: &[Npc]) -> Text<'static> {
        let mut lines = Vec::with_capacity(self.height);
        for (y, row) in self.tiles.iter().enumerate() {
            let mut spans = Vec::with_capacity(row.len());
            for (x, tile) in row.iter().enumerate() {
                let (ch, color) = glyph_at(x, y, tile, player, npcs);
                spans.push(Span::styled(ch.to_string(), color));
            }
            lines.push(Line::from(spans));
        }
        Text::from(lines)
    }

    #[allow(dead_code)]
    pub fn fill_rect(&mut self, x: usize, y: usize, w: usize, h: usize, ch: char) {
        for dy in 0..h {
            for dx in 0..w {
                self.set_tile(x + dx, y + dy, ch);
            }
        }
    }

    #[allow(dead_code)]
    pub fn set_tile(&mut self, x: usize, y: usize, ch: char) {
        self.set_colored(x, y, ch, default_color(ch));
    }

    pub fn set_colored(&mut self, x: usize, y: usize, ch: char, color: Color) {
        if y < self.height && x < self.width {
            self.tiles[y][x] = Tile { ch, color };
        }
    }

    #[allow(dead_code)]
    pub fn replace_rows(&mut self, start_y: usize, new_lines: &[&str]) {
        self.play_lines(0, start_y, new_lines);
    }

    fn drain_ready(&mut self) {
        if !self.pause_left.is_zero() {
            return;
        }
        while let Some(step) = self.steps.front() {
            match step {
                Step::Pause(duration) => {
                    self.pause_left = *duration;
                    self.steps.pop_front();
                    return;
                }
                Step::Paint(_) => {
                    let Some(Step::Paint(paints)) = self.steps.pop_front() else {
                        return;
                    };
                    self.apply(&paints);
                }
            }
        }
    }

    fn apply(&mut self, paints: &[Paint]) {
        for paint in paints {
            self.set_colored(paint.x, paint.y, paint.ch, paint.color);
        }
    }
}

fn glyph_at(x: usize, y: usize, tile: &Tile, player: &Player, npcs: &[Npc]) -> (char, Color) {
    if x == player.x && y == player.y {
        ('@', Color::Yellow)
    } else if let Some(npc) = npcs.iter().find(|n| n.present && n.x == x && n.y == y) {
        (npc.symbol, Color::White)
    } else {
        (tile.ch, tile.color)
    }
}

fn default_color(ch: char) -> Color {
    match ch {
        '#' => Color::DarkGray,
        _ => Color::White,
    }
}

fn events_from_lines(origin_x: usize, origin_y: usize, lines: &[&str]) -> Vec<MapEvent> {
    let mut events = Vec::new();
    for (row, line) in lines.iter().enumerate() {
        let mut ink = Ink::Auto;
        let mut x = 0;
        for token in tokenize(line) {
            match token {
                Token::Color(color) => ink = Ink::Fixed(color),
                Token::Auto => ink = Ink::Auto,
                Token::Pause(duration) => events.push(MapEvent::Pause(duration)),
                Token::Char(ch) => {
                    let color = match ink {
                        Ink::Auto => default_color(ch),
                        Ink::Fixed(color) => color,
                    };
                    events.push(MapEvent::set(origin_x + x, origin_y + row, ch, color));
                    x += 1;
                }
            }
        }
    }
    events
}

fn tokenize(line: &str) -> Vec<Token> {
    let mut tokens = Vec::new();
    let mut chars = line.chars().peekable();
    while let Some(ch) = chars.next() {
        if ch != '{' {
            tokens.push(Token::Char(ch));
            continue;
        }
        let mut tag = String::new();
        let mut closed = false;
        for c in chars.by_ref() {
            if c == '}' {
                closed = true;
                break;
            }
            tag.push(c);
        }
        if !closed {
            panic!("map markup is missing '}}' in `{line}`");
        }
        tokens.push(parse_tag(&tag, line));
    }
    tokens
}

fn parse_tag(tag: &str, line: &str) -> Token {
    let tag = tag.trim();
    let lower = tag.to_ascii_lowercase();
    if lower == "auto" {
        return Token::Auto;
    }
    if let Some(ms) = lower
        .strip_prefix("p:")
        .or_else(|| lower.strip_prefix("pause:"))
    {
        let ms: u64 = ms.trim().parse().unwrap_or_else(|_| {
            panic!("map pause `{tag}` in `{line}` needs a number of milliseconds")
        });
        return Token::Pause(Duration::from_millis(ms));
    }
    let color = match lower.as_str() {
        "w" | "white" => Color::White,
        "k" | "black" => Color::Black,
        "r" | "red" => Color::Red,
        "g" | "green" => Color::Green,
        "y" | "yellow" => Color::Yellow,
        "b" | "blue" => Color::Blue,
        "c" | "cyan" => Color::Cyan,
        "m" | "magenta" => Color::Magenta,
        "d" | "darkgray" | "darkgrey" => Color::DarkGray,
        "a" | "gray" | "grey" => Color::Gray,
        _ => panic!("unknown map markup `{{{tag}}}` in `{line}`"),
    };
    Token::Color(color)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn color_markup_colors_characters_without_adding_tiles() {
        let map = Map::from_strings(&["{red}AB{white}C", "D"]);
        assert_eq!(map.width, 3);
        assert_eq!(map.height, 2);
        assert_eq!(
            map.tiles[0][0],
            Tile {
                ch: 'A',
                color: Color::Red
            }
        );
        assert_eq!(
            map.tiles[0][1],
            Tile {
                ch: 'B',
                color: Color::Red
            }
        );
        assert_eq!(
            map.tiles[0][2],
            Tile {
                ch: 'C',
                color: Color::White
            }
        );
        assert_eq!(
            map.tiles[1][0],
            Tile {
                ch: 'D',
                color: Color::White
            }
        );
        assert!(!map.is_busy());
    }

    #[test]
    fn walls_default_to_dark_gray() {
        let map = Map::from_strings(&["#."]);
        assert_eq!(map.tiles[0][0].color, Color::DarkGray);
        assert_eq!(map.tiles[0][1].color, Color::White);
        assert!(map.is_walkable(1, 0));
        assert!(!map.is_walkable(0, 0));
    }

    #[test]
    fn pause_in_the_text_holds_the_later_characters() {
        let mut map = Map::from_strings(&["A{p:100}{red}B"]);
        assert_eq!(map.tiles[0][0].ch, 'A');
        assert_eq!(map.tiles[0][1].ch, ' ');
        assert!(map.is_busy());

        map.tick(Duration::from_millis(99));
        assert_eq!(map.tiles[0][1].ch, ' ');

        map.tick(Duration::from_millis(1));
        assert_eq!(
            map.tiles[0][1],
            Tile {
                ch: 'B',
                color: Color::Red
            }
        );
        assert!(!map.is_busy());
    }

    #[test]
    fn play_repaints_one_cell_after_a_pause() {
        let mut map = Map::from_strings(&[".."]);
        map.play([MapEvent::pause(10), MapEvent::set(1, 0, '!', Color::Red)]);
        assert!(map.is_busy());
        assert_eq!(map.tiles[0][1].ch, '.');

        map.tick(Duration::from_millis(10));
        assert_eq!(
            map.tiles[0][1],
            Tile {
                ch: '!',
                color: Color::Red
            }
        );
        assert!(!map.is_busy());
    }
}
