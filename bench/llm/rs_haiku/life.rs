use std::io::{self, Read, Write};

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).expect("read stdin");
    let mut lines = input.lines();

    let header = lines.next().unwrap_or("");
    let mut nums = header
        .split_whitespace()
        .map(|t| t.parse::<usize>().expect("integer"));
    let h = nums.next().unwrap();
    let w = nums.next().unwrap();
    let t = nums.next().unwrap();

    let mut grid = vec![vec![false; w]; h];
    for r in 0..h {
        let row: &[u8] = lines.next().unwrap_or("").as_bytes();
        for c in 0..w {
            grid[r][c] = row.get(c) == Some(&b'#');
        }
    }

    for _ in 0..t {
        let mut next = vec![vec![false; w]; h];
        for r in 0..h {
            let up = (r + h - 1) % h;
            let down = (r + 1) % h;
            for c in 0..w {
                let left = (c + w - 1) % w;
                let right = (c + 1) % w;
                let neighbours = [
                    grid[up][left],
                    grid[up][c],
                    grid[up][right],
                    grid[r][left],
                    grid[r][right],
                    grid[down][left],
                    grid[down][c],
                    grid[down][right],
                ]
                .iter()
                .filter(|&&alive| alive)
                .count();
                next[r][c] = matches!(
                    (grid[r][c], neighbours),
                    (true, 2) | (true, 3) | (false, 3)
                );
            }
        }
        grid = next;
    }

    let stdout = io::stdout();
    let mut out = io::BufWriter::new(stdout.lock());
    for row in &grid {
        let line: String = row
            .iter()
            .map(|&alive| if alive { '#' } else { '.' })
            .collect();
        writeln!(out, "{}", line).unwrap();
    }
}
