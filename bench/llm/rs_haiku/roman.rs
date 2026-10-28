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
    for &(value, symbol) in TABLE.iter() {
        while n >= value {
            s.push_str(symbol);
            n -= value;
        }
    }
    s
}

fn roman_digit(c: u8) -> Option<u32> {
    match c {
        b'I' => Some(1),
        b'V' => Some(5),
        b'X' => Some(10),
        b'L' => Some(50),
        b'C' => Some(100),
        b'D' => Some(500),
        b'M' => Some(1000),
        _ => None,
    }
}

/// Value of a Roman numeral written with subtractive pairs (no validation of form).
fn roman_value(s: &[u8]) -> Option<u32> {
    let digits: Vec<u32> = s
        .iter()
        .map(|&c| roman_digit(c))
        .collect::<Option<Vec<u32>>>()?;
    let mut total: i64 = 0;
    for i in 0..digits.len() {
        if i + 1 < digits.len() && digits[i] < digits[i + 1] {
            total -= digits[i] as i64;
        } else {
            total += digits[i] as i64;
        }
    }
    u32::try_from(total).ok()
}

fn classify(line: &str) -> String {
    let bytes = line.as_bytes();
    if bytes.iter().all(|c| c.is_ascii_digit()) {
        if bytes[0] == b'0' {
            return "invalid".to_string();
        }
        match line.parse::<u32>() {
            Ok(n) if (1..=3999).contains(&n) => to_roman(n),
            _ => "invalid".to_string(),
        }
    } else {
        match roman_value(bytes) {
            // Only the standard form is accepted: re-rendering must give back the same text.
            Some(v) if (1..=3999).contains(&v) && to_roman(v) == line => v.to_string(),
            _ => "invalid".to_string(),
        }
    }
}

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).expect("read stdin");
    let stdout = io::stdout();
    let mut out = io::BufWriter::new(stdout.lock());

    for line in input.lines() {
        if line.is_empty() {
            continue;
        }
        writeln!(out, "{}", classify(line)).unwrap();
    }
}
