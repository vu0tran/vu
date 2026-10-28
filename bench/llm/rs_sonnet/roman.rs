use std::io::{self, Read, Write};

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

fn to_roman(mut n: u32) -> String {
    let mut s = String::new();
    for &(v, r) in TABLE.iter() {
        while n >= v {
            s.push_str(r);
            n -= v;
        }
    }
    s
}

fn digit_value(c: u8) -> u32 {
    match c {
        b'I' => 1,
        b'V' => 5,
        b'X' => 10,
        b'L' => 50,
        b'C' => 100,
        b'D' => 500,
        _ => 1000,
    }
}

fn from_roman(s: &str) -> Option<u32> {
    let b = s.as_bytes();
    let mut total: i64 = 0;
    for i in 0..b.len() {
        let v = digit_value(b[i]) as i64;
        let next = if i + 1 < b.len() { digit_value(b[i + 1]) as i64 } else { 0 };
        if v < next {
            total -= v;
        } else {
            total += v;
        }
    }
    if total < 1 || total > 3999 {
        return None;
    }
    let n = total as u32;
    if to_roman(n) == s {
        Some(n)
    } else {
        None
    }
}

fn convert(line: &str) -> String {
    if line.bytes().all(|b| b.is_ascii_digit()) {
        if line.starts_with('0') || line.len() > 4 {
            return "invalid".to_string();
        }
        let n: u32 = line.parse().unwrap();
        if (1..=3999).contains(&n) {
            to_roman(n)
        } else {
            "invalid".to_string()
        }
    } else if line.bytes().all(|b| b"IVXLCDM".contains(&b)) {
        match from_roman(line) {
            Some(n) => n.to_string(),
            None => "invalid".to_string(),
        }
    } else {
        "invalid".to_string()
    }
}

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).unwrap();
    let out = io::stdout();
    let mut out = out.lock();
    for line in input.lines() {
        let line = line.strip_suffix('\r').unwrap_or(line);
        if line.is_empty() {
            continue;
        }
        writeln!(out, "{}", convert(line)).unwrap();
    }
}
