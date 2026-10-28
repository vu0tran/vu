use std::collections::{BTreeMap, HashMap};
use std::io::{self, Read, Write};

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).expect("read stdin");
    let stdout = io::stdout();
    let mut out = io::BufWriter::new(stdout.lock());

    let mut lines = input.lines().map(str::trim).filter(|l| !l.is_empty());
    let cap: usize = match lines.next() {
        Some(l) => l.parse().expect("capacity"),
        None => return,
    };

    // key -> (value, last-use stamp); stamp -> key gives the LRU order.
    let mut map: HashMap<i64, (i64, u64)> = HashMap::new();
    let mut order: BTreeMap<u64, i64> = BTreeMap::new();
    let mut clock: u64 = 0;

    for line in lines {
        let mut parts = line.split_whitespace();
        match parts.next() {
            Some("get") => {
                let k: i64 = parts.next().unwrap().parse().unwrap();
                match map.get_mut(&k) {
                    Some(entry) => {
                        order.remove(&entry.1);
                        clock += 1;
                        entry.1 = clock;
                        order.insert(clock, k);
                        writeln!(out, "{}", entry.0).unwrap();
                    }
                    None => writeln!(out, "-1").unwrap(),
                }
            }
            Some("put") => {
                let k: i64 = parts.next().unwrap().parse().unwrap();
                let v: i64 = parts.next().unwrap().parse().unwrap();
                clock += 1;
                match map.get_mut(&k) {
                    Some(entry) => {
                        order.remove(&entry.1);
                        *entry = (v, clock);
                    }
                    None => {
                        map.insert(k, (v, clock));
                    }
                }
                order.insert(clock, k);
                if map.len() > cap {
                    if let Some((_, old_key)) = order.pop_first() {
                        map.remove(&old_key);
                    }
                }
            }
            _ => {}
        }
    }
}
