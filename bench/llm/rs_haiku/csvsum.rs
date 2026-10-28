use std::collections::HashMap;
use std::io::{self, Read, Write};

/// Splits one CSV record into fields, honouring double quotes and doubled quotes.
fn split_csv(line: &str) -> Vec<String> {
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
        } else {
            match c {
                '"' => in_quotes = true,
                ',' => fields.push(std::mem::take(&mut cur)),
                _ => cur.push(c),
            }
        }
    }
    fields.push(cur);
    fields
}

/// Parses a decimal with at most 2 fraction digits into an integer number of cents.
fn parse_cents(s: &str) -> Option<i64> {
    let (negative, rest) = if let Some(r) = s.strip_prefix('-') {
        (true, r)
    } else if let Some(r) = s.strip_prefix('+') {
        (false, r)
    } else {
        (false, s)
    };
    let (int_part, frac_part) = match rest.split_once('.') {
        Some((a, b)) => (a, b),
        None => (rest, ""),
    };
    if int_part.is_empty() && frac_part.is_empty() {
        return None;
    }
    if !int_part.bytes().all(|b| b.is_ascii_digit())
        || !frac_part.bytes().all(|b| b.is_ascii_digit())
        || frac_part.len() > 2
    {
        return None;
    }
    let whole: i64 = if int_part.is_empty() {
        0
    } else {
        int_part.parse().ok()?
    };
    let frac: i64 = match frac_part.len() {
        0 => 0,
        1 => frac_part.parse::<i64>().ok()? * 10,
        _ => frac_part.parse().ok()?,
    };
    let value = whole * 100 + frac;
    Some(if negative { -value } else { value })
}

fn format_cents(v: i64) -> String {
    let sign = if v < 0 { "-" } else { "" };
    let a = v.abs();
    format!("{}{}.{:02}", sign, a / 100, a % 100)
}

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).expect("read stdin");
    let mut lines = input.lines();

    let header = match lines.next() {
        Some(h) => split_csv(h),
        None => return,
    };
    let region_col = header
        .iter()
        .position(|h| h.trim() == "region")
        .expect("region column");
    let amount_col = header
        .iter()
        .position(|h| h.trim() == "amount")
        .expect("amount column");

    // Regions in order of first appearance, with their running totals in cents.
    let mut index: HashMap<String, usize> = HashMap::new();
    let mut totals: Vec<(String, i64)> = Vec::new();

    for line in lines {
        if line.is_empty() {
            continue;
        }
        let fields = split_csv(line);
        let region = fields.get(region_col).map(String::as_str).unwrap_or("");
        let amount = fields
            .get(amount_col)
            .and_then(|a| parse_cents(a.trim()))
            .unwrap_or(0);
        let slot = match index.get(region) {
            Some(&i) => i,
            None => {
                totals.push((region.to_string(), 0));
                index.insert(region.to_string(), totals.len() - 1);
                totals.len() - 1
            }
        };
        totals[slot].1 += amount;
    }

    let stdout = io::stdout();
    let mut out = io::BufWriter::new(stdout.lock());
    for (region, cents) in &totals {
        writeln!(out, "{} {}", region, format_cents(*cents)).unwrap();
    }
}
