use std::collections::HashMap;
use std::io::{self, Read, Write};

fn to_roman(mut n: u32) -> String {
    const TABLE: [(u32, &str); 13] = [
        (1000, "M"),
        (900, "CM"),
        (500, "D"),
        (400, "CD"),
        (100, "C"),
        (90, "XC"),
        (50, "L"),
        (40, "XL"),
        (10, "X"),
        (9, "IX"),
        (5, "V"),
        (4, "IV"),
        (1, "I"),
    ];
    let mut s = String::new();
    for &(v, sym) in TABLE.iter() {
        while n >= v {
            s.push_str(sym);
            n -= v;
        }
    }
    s
}

fn main() {
    let mut data = Vec::new();
    io::stdin().read_to_end(&mut data).unwrap();

    let romans: HashMap<String, u32> = (1..=3999).map(|n| (to_roman(n), n)).collect();

    let stdout = io::stdout();
    let mut out = io::BufWriter::new(stdout.lock());
    for raw in data.split(|&b| b == b'\n') {
        let line = raw.strip_suffix(b"\r").unwrap_or(raw);
        if line.is_empty() {
            continue;
        }
        if line.iter().all(|b| b.is_ascii_digit()) {
            if line[0] == b'0' || line.len() > 4 {
                writeln!(out, "invalid").unwrap();
                continue;
            }
            let n: u32 = line.iter().fold(0, |acc, &b| acc * 10 + (b - b'0') as u32);
            if (1..=3999).contains(&n) {
                writeln!(out, "{}", to_roman(n)).unwrap();
            } else {
                writeln!(out, "invalid").unwrap();
            }
            continue;
        }
        match std::str::from_utf8(line).ok().and_then(|s| romans.get(s)) {
            Some(v) => writeln!(out, "{}", v).unwrap(),
            None => writeln!(out, "invalid").unwrap(),
        }
    }
}
