use std::collections::HashMap;
use std::io::{self, Read, Write};

fn main() {
    let mut data = Vec::new();
    io::stdin().read_to_end(&mut data).unwrap();

    let mut counts: HashMap<String, u64> = HashMap::new();
    let mut cur = String::new();
    for &b in &data {
        if b.is_ascii_alphabetic() {
            cur.push(b.to_ascii_lowercase() as char);
        } else if !cur.is_empty() {
            *counts.entry(std::mem::take(&mut cur)).or_insert(0) += 1;
        }
    }
    if !cur.is_empty() {
        *counts.entry(cur).or_insert(0) += 1;
    }

    let mut items: Vec<(String, u64)> = counts.into_iter().collect();
    items.sort_by(|a, b| b.1.cmp(&a.1).then_with(|| a.0.cmp(&b.0)));

    let stdout = io::stdout();
    let mut out = io::BufWriter::new(stdout.lock());
    for (w, c) in items.iter().take(10) {
        writeln!(out, "{} {}", w, c).unwrap();
    }
}
