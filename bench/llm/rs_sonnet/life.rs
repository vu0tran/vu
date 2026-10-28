use std::io::{self, Read, Write};

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).unwrap();
    let mut it = input.split_ascii_whitespace();
    let h: usize = it.next().unwrap().parse().unwrap();
    let w: usize = it.next().unwrap().parse().unwrap();
    let t: usize = it.next().unwrap().parse().unwrap();
    let mut grid: Vec<Vec<bool>> = Vec::with_capacity(h);
    for _ in 0..h {
        let row = it.next().unwrap_or("");
        let mut r: Vec<bool> = row.bytes().map(|b| b == b'#').collect();
        r.resize(w, false);
        grid.push(r);
    }
    for _ in 0..t {
        let mut next = vec![vec![false; w]; h];
        for y in 0..h {
            for x in 0..w {
                let mut n = 0;
                for dy in [h - 1, 0, 1] {
                    for dx in [w - 1, 0, 1] {
                        if dy == 0 && dx == 0 {
                            continue;
                        }
                        if grid[(y + dy) % h][(x + dx) % w] {
                            n += 1;
                        }
                    }
                }
                next[y][x] = matches!((grid[y][x], n), (true, 2) | (true, 3) | (false, 3));
            }
        }
        grid = next;
    }
    let out = io::stdout();
    let mut out = out.lock();
    for row in &grid {
        let s: String = row.iter().map(|&c| if c { '#' } else { '.' }).collect();
        writeln!(out, "{}", s).unwrap();
    }
}
