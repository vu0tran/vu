use std::io::{self, Read, Write};

/// Returns None if the line is balanced, otherwise the 1-based error position.
fn check(line: &[u8]) -> Option<usize> {
    let mut stack: Vec<u8> = Vec::new();
    for (i, &b) in line.iter().enumerate() {
        match b {
            b'(' | b'[' | b'{' => stack.push(b),
            b')' | b']' | b'}' => {
                let open = match b {
                    b')' => b'(',
                    b']' => b'[',
                    _ => b'{',
                };
                if stack.last() == Some(&open) {
                    stack.pop();
                } else {
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
    let mut input = Vec::new();
    io::stdin().read_to_end(&mut input).expect("read stdin");
    let stdout = io::stdout();
    let mut out = io::BufWriter::new(stdout.lock());

    if !input.is_empty() {
        let all: &[u8] = &input;
        // A final newline terminates the last line; it does not start another.
        let body = all.strip_suffix(b"\n").unwrap_or(all);
        for line in body.split(|&b| b == b'\n') {
            match check(line) {
                None => writeln!(out, "ok").unwrap(),
                Some(pos) => writeln!(out, "error at {}", pos).unwrap(),
            }
        }
    }
}
