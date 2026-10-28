use std::collections::HashMap;
use std::io::{self, Read, Write};

fn parse_csv_line(line: &str) -> Vec<String> {
    let mut fields = Vec::new();
    let mut cur = String::new();
    let mut chars = line.chars().peekable();
    let mut in_quotes = false;
    let mut at_field_start = true;

    while let Some(c) = chars.next() {
        if in_quotes {
            if c == '"' {
                if chars.peek() == Some(&'"') {
                    chars.next();
                    cur.push('"');
                } else {
                    in_quotes = false;
                }
            } else {
                cur.push(c);
            }
        } else if c == ',' {
            fields.push(std::mem::take(&mut cur));
            at_field_start = true;
            continue;
        } else if c == '"' && at_field_start {
            in_quotes = true;
        } else {
            cur.push(c);
        }
        at_field_start = false;
    }
    fields.push(cur);
    fields
}

/// Parses a decimal with at most 2 fractional digits into hundredths.
fn parse_cents(s: &str) -> Option<i64> {
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
    if int_part.is_empty() && frac_part.is_empty() {
        return None;
    }
    if !int_part.bytes().all(|b| b.is_ascii_digit())
        || !frac_part.bytes().all(|b| b.is_ascii_digit())
        || frac_part.len() > 2
    {
        return None;
    }
    let whole: i64 = if int_part.is_empty() { 0 } else { int_part.parse().ok()? };
    let mut frac: i64 = if frac_part.is_empty() { 0 } else { frac_part.parse().ok()? };
    if frac_part.len() == 1 {
        frac *= 10;
    }
    let v = whole.checked_mul(100)?.checked_add(frac)?;
    Some(if neg { -v } else { v })
}

fn format_cents(v: i64) -> String {
    let sign = if v < 0 { "-" } else { "" };
    let a = v.unsigned_abs();
    format!("{}{}.{:02}", sign, a / 100, a % 100)
}

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).unwrap();
    let mut lines = input.lines().filter(|l| !l.is_empty());

    let header = match lines.next() {
        Some(h) => parse_csv_line(h),
        None => return,
    };
    let region_idx = header.iter().position(|h| h.trim() == "region");
    let amount_idx = header.iter().position(|h| h.trim() == "amount");
    let (region_idx, amount_idx) = match (region_idx, amount_idx) {
        (Some(r), Some(a)) => (r, a),
        _ => return,
    };

    let mut order: Vec<String> = Vec::new();
    let mut totals: HashMap<String, i64> = HashMap::new();
    for line in lines {
        let fields = parse_csv_line(line);
        let (Some(region), Some(amount)) = (fields.get(region_idx), fields.get(amount_idx)) else {
            continue;
        };
        let cents = parse_cents(amount).unwrap_or(0);
        match totals.get_mut(region) {
            Some(t) => *t += cents,
            None => {
                order.push(region.clone());
                totals.insert(region.clone(), cents);
            }
        }
    }

    let stdout = io::stdout();
    let mut out = io::BufWriter::new(stdout.lock());
    for r in &order {
        writeln!(out, "{} {}", r, format_cents(totals[r])).unwrap();
    }
}
