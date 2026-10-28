use super::npc::Npc;
use super::player::Player;

#[derive(Clone)]
pub struct Map {
    pub tiles: Vec<Vec<char>>,
    pub width: usize,
    pub height: usize,
}

impl Map {
    pub fn from_strings(lines: &[&str]) -> Self {
        let tiles: Vec<Vec<char>> = lines.iter().map(|l| l.chars().collect()).collect();
        let height = tiles.len();
        let width = tiles.first().map(|r| r.len()).unwrap_or(0);
        Self {
            tiles,
            width,
            height,
        }
    }

    pub fn is_walkable(&self, x: usize, y: usize) -> bool {
        if y >= self.height || x >= self.width {
            return false;
        }
        self.tiles[y][x] == '.'
    }

    pub fn render(&self, player: &Player, npcs: &[Npc]) -> String {
        let mut out = String::new();
        for (y, row) in self.tiles.iter().enumerate() {
            for (x, &ch) in row.iter().enumerate() {
                if x == player.x && y == player.y {
                    out.push('@');
                } else if let Some(npc) = npcs.iter().find(|n| n.x == x && n.y == y) {
                    out.push(npc.symbol);
                } else {
                    out.push(ch);
                }
            }
            out.push('\n');
        }
        out
    }

    pub fn fill_rect(&mut self, x: usize, y: usize, w: usize, h: usize, ch: char) {
        for dy in 0..h {
            let yy = y + dy;
            if yy >= self.height {
                break;
            }
            for dx in 0..w {
                let xx = x + dx;
                if xx >= self.width {
                    break;
                }
                self.tiles[yy][xx] = ch;
            }
        }
    }

    pub fn set_tile(&mut self, x: usize, y: usize, ch: char) {
        if y < self.height && x < self.width {
            self.tiles[y][x] = ch;
        }
    }

    pub fn replace_rows(&mut self, start_y: usize, new_lines: &[&str]) {
        for (i, line) in new_lines.iter().enumerate() {
            let y = start_y + i;
            if y >= self.height {
                break;
            }
            let chars: Vec<char> = line.chars().collect();
            for (x, &ch) in chars.iter().enumerate() {
                if x < self.width {
                    self.tiles[y][x] = ch;
                }
            }
        }
    }
}
