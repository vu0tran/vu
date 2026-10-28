use std::collections::HashMap;
use std::io::{self, Read, Write};

fn main() {
    let mut input = Vec::new();
    io::stdin().read_to_end(&mut input).expect("read stdin");

    let mut counts: HashMap<String, u64> = HashMap::new();
    let mut current = String::new();
    for &b in &input {
        if b.is_ascii_alphabetic() {
            current.push(b.to_ascii_lowercase() as char);
        } else if !current.is_empty() {
            *counts.entry(std::mem::take(&mut current)).or_insert(0) += 1;
        }
    }
    if !current.is_empty() {
        *counts.entry(current).or_insert(0) += 1;
    }

    let mut words: Vec<(String, u64)> = counts.into_iter().collect();
    words.sort_by(|a, b| b.1.cmp(&a.1).then_with(|| a.0.cmp(&b.0)));

    let stdout = io::stdout();
    let mut out = io::BufWriter::new(stdout.lock());
    for (word, count) in words.iter().take(10) {
        writeln!(out, "{} {}", word, count).unwrap();
    }
}
