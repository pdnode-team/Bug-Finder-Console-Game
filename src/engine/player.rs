use super::map::Map;

pub struct Player {
    pub x: usize,
    pub y: usize,
}

impl Player {
    pub fn try_move(&mut self, dx: i32, dy: i32, map: &Map) -> bool {
        let nx = self.x as i32 + dx;
        let ny = self.y as i32 + dy;
        if nx < 0 || ny < 0 {
            return false;
        }
        let (nx, ny) = (nx as usize, ny as usize);
        if map.is_walkable(nx, ny) {
            self.x = nx;
            self.y = ny;
            true
        } else {
            false
        }
    }
}
