#[derive(Clone)]
pub struct Npc {
    pub symbol: char,
    pub x: usize,
    pub y: usize,
    pub dialog: Vec<String>,
    pub dialog_index: usize,
}

impl Npc {
    pub fn new(symbol: char, x: usize, y: usize, dialog: Vec<&str>) -> Self {
        Self {
            symbol,
            x,
            y,
            dialog: dialog.into_iter().map(|s| s.to_string()).collect(),
            dialog_index: 0,
        }
    }

    pub fn current_line(&self) -> &str {
        self.dialog
            .get(self.dialog_index)
            .map(|s| s.as_str())
            .unwrap_or("")
    }

    pub fn advance(&mut self) -> bool {
        if self.dialog_index + 1 < self.dialog.len() {
            self.dialog_index += 1;
            true
        } else {
            false
        }
    }

    pub fn reset(&mut self) {
        self.dialog_index = 0;
    }

    pub fn is_adjacent(&self, px: usize, py: usize) -> bool {
        let dx = (self.x as i32 - px as i32).abs();
        let dy = (self.y as i32 - py as i32).abs();
        dx <= 1 && dy <= 1 && !(dx == 0 && dy == 0)
    }
}
