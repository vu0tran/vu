use std::io::{self, Read, Write};

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).unwrap();
    let mut lines = input.lines();

    let header = lines.next().unwrap();
    let mut nums = header.split_ascii_whitespace().map(|t| t.parse::<usize>().unwrap());
    let h = nums.next().unwrap();
    let w = nums.next().unwrap();
    let t = nums.next().unwrap();

    let mut grid = vec![false; h * w];
    for r in 0..h {
        let line = lines.next().unwrap_or("").as_bytes();
        for c in 0..w {
            grid[r * w + c] = line.get(c) == Some(&b'#');
        }
    }

    let mut next = vec![false; h * w];
    for _ in 0..t {
        for r in 0..h {
            let up = (r + h - 1) % h;
            let down = (r + 1) % h;
            for c in 0..w {
                let left = (c + w - 1) % w;
                let right = (c + 1) % w;
                let n = [
                    grid[up * w + left],
                    grid[up * w + c],
                    grid[up * w + right],
                    grid[r * w + left],
                    grid[r * w + right],
                    grid[down * w + left],
                    grid[down * w + c],
                    grid[down * w + right],
                ]
                .iter()
                .filter(|&&x| x)
                .count();
                let alive = grid[r * w + c];
                next[r * w + c] = n == 3 || (alive && n == 2);
            }
        }
        std::mem::swap(&mut grid, &mut next);
    }

    let stdout = io::stdout();
    let mut out = io::BufWriter::new(stdout.lock());
    let mut row = String::with_capacity(w);
    for r in 0..h {
        row.clear();
        for c in 0..w {
            row.push(if grid[r * w + c] { '#' } else { '.' });
        }
        writeln!(out, "{}", row).unwrap();
    }
}
