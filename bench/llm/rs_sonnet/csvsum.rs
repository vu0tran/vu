use std::collections::HashMap;
use std::io::{self, Read, Write};

fn parse_fields(line: &str) -> Vec<String> {
    let mut fields = Vec::new();
    let mut cur = String::new();
    let mut in_quotes = false;
    let mut chars = line.chars().peekable();
    while let Some(c) = chars.next() {
        if in_quotes {
            if c == '"' {
                if chars.peek() == Some(&'"') {
                    cur.push('"');
                    chars.next();
                } else {
                    in_quotes = false;
                }
            } else {
                cur.push(c);
            }
        } else if c == '"' {
            in_quotes = true;
        } else if c == ',' {
            fields.push(std::mem::take(&mut cur));
        } else {
            cur.push(c);
        }
    }
    fields.push(cur);
    fields
}

fn parse_cents(s: &str) -> i64 {
    let s = s.trim();
    let (neg, rest) = if let Some(r) = s.strip_prefix('-') {
        (true, r)
    } else if let Some(r) = s.strip_prefix('+') {
        (false, r)
    } else {
        (false, s)
    };
    let (int_part, frac_part) = match rest.split_once('.') {
        Some((i, f)) => (i, f),
        None => (rest, ""),
    };
    let ip: i64 = if int_part.is_empty() { 0 } else { int_part.parse().unwrap_or(0) };
    let mut fp: i64 = 0;
    let mut digits = 0;
    for c in frac_part.chars().take(2) {
        fp = fp * 10 + c.to_digit(10).unwrap_or(0) as i64;
        digits += 1;
    }
    while digits < 2 {
        fp *= 10;
        digits += 1;
    }
    let v = ip * 100 + fp;
    if neg {
        -v
    } else {
        v
    }
}

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).unwrap();
    let mut lines = input.lines();
    let header = match lines.next() {
        Some(h) => parse_fields(h.strip_suffix('\r').unwrap_or(h)),
        None => return,
    };
    let ri = header.iter().position(|h| h.trim() == "region");
    let ai = header.iter().position(|h| h.trim() == "amount");
    let (ri, ai) = match (ri, ai) {
        (Some(r), Some(a)) => (r, a),
        _ => return,
    };
    let mut order: Vec<String> = Vec::new();
    let mut totals: HashMap<String, i64> = HashMap::new();
    for line in lines {
        let line = line.strip_suffix('\r').unwrap_or(line);
        if line.is_empty() {
            continue;
        }
        let f = parse_fields(line);
        let region = f.get(ri).cloned().unwrap_or_default();
        let amount = f.get(ai).map(|a| parse_cents(a)).unwrap_or(0);
        if !totals.contains_key(&region) {
            order.push(region.clone());
        }
        *totals.entry(region).or_insert(0) += amount;
    }
    let out = io::stdout();
    let mut out = out.lock();
    for r in &order {
        let t = totals[r];
        let sign = if t < 0 { "-" } else { "" };
        let a = t.abs();
        writeln!(out, "{} {}{}.{:02}", r, sign, a / 100, a % 100).unwrap();
    }
}
