use std::io::{self, Read, Write};

fn check(line: &[u8]) -> Option<usize> {
    let mut stack: Vec<u8> = Vec::new();
    for (i, &c) in line.iter().enumerate() {
        match c {
            b'(' | b'[' | b'{' => stack.push(c),
            b')' | b']' | b'}' => {
                let want = match c {
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
    if data.is_empty() {
        return;
    }
    let body: &[u8] = if data.last() == Some(&b'\n') {
        &data[..data.len() - 1]
    } else {
        &data[..]
    };

    let stdout = io::stdout();
    let mut out = io::BufWriter::new(stdout.lock());
    for line in body.split(|&b| b == b'\n') {
        match check(line) {
            None => writeln!(out, "ok").unwrap(),
            Some(n) => writeln!(out, "error at {}", n).unwrap(),
        }
    }
}
