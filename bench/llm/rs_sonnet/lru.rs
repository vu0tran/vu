use std::collections::{BTreeMap, HashMap};
use std::io::{self, BufRead, Write};

fn main() {
    let stdin = io::stdin();
    let mut lines = stdin.lock().lines();
    let cap: usize = lines
        .next()
        .unwrap()
        .unwrap()
        .trim()
        .parse()
        .unwrap();
    // key -> (value, stamp); stamp -> key (ordered by recency)
    let mut map: HashMap<i64, (i64, u64)> = HashMap::new();
    let mut order: BTreeMap<u64, i64> = BTreeMap::new();
    let mut clock: u64 = 0;
    let out = io::stdout();
    let mut out = out.lock();
    for line in lines {
        let line = line.unwrap();
        let mut parts = line.split_ascii_whitespace();
        let cmd = match parts.next() {
            Some(c) => c,
            None => continue,
        };
        match cmd {
            "get" => {
                let k: i64 = parts.next().unwrap().parse().unwrap();
                if let Some(entry) = map.get_mut(&k) {
                    clock += 1;
                    order.remove(&entry.1);
                    entry.1 = clock;
                    order.insert(clock, k);
                    writeln!(out, "{}", entry.0).unwrap();
                } else {
                    writeln!(out, "-1").unwrap();
                }
            }
            "put" => {
                let k: i64 = parts.next().unwrap().parse().unwrap();
                let v: i64 = parts.next().unwrap().parse().unwrap();
                clock += 1;
                if let Some(entry) = map.get_mut(&k) {
                    order.remove(&entry.1);
                    *entry = (v, clock);
                } else {
                    map.insert(k, (v, clock));
                }
                order.insert(clock, k);
                if map.len() > cap {
                    if let Some((&stamp, &old)) = order.iter().next() {
                        order.remove(&stamp);
                        map.remove(&old);
                    }
                }
            }
            _ => {}
        }
    }
}
