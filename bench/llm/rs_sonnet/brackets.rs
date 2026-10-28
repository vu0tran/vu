use std::io::{self, Read, Write};

fn check(line: &[u8]) -> Option<usize> {
    let mut stack: Vec<u8> = Vec::new();
    for (i, &b) in line.iter().enumerate() {
        match b {
            b'(' | b'[' | b'{' => stack.push(b),
            b')' | b']' | b'}' => {
                let want = match b {
                    b')' => b'(',
                    b']' => b'[',
                    _ => b'{',
                };
                if stack.pop() != Some(want) {
                    return Some(i + 1);
                }
            }
            _ => {}
        }
    }
    if stack.is_empty() {
        None
    } else {
        Some(line.len() + 1)
    }
}

fn main() {
    let mut data = Vec::new();
    io::stdin().read_to_end(&mut data).unwrap();
    let mut lines: Vec<&[u8]> = data.split(|&b| b == b'\n').collect();
    if let Some(last) = lines.last() {
        if last.is_empty() {
            lines.pop();
        }
    }
    let out = io::stdout();
    let mut out = out.lock();
    for line in lines {
        match check(line) {
            None => writeln!(out, "ok").unwrap(),
            Some(n) => writeln!(out, "error at {}", n).unwrap(),
        }
    }
}
