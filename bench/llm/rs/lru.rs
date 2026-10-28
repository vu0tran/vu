use std::collections::{BTreeMap, HashMap};
use std::io::{self, Read, Write};

struct Lru {
    cap: usize,
    clock: u64,
    map: HashMap<i64, (i64, u64)>,
    order: BTreeMap<u64, i64>,
}

impl Lru {
    fn new(cap: usize) -> Self {
        Lru { cap, clock: 0, map: HashMap::new(), order: BTreeMap::new() }
    }

    fn touch(&mut self, key: i64) -> u64 {
        self.clock += 1;
        self.order.insert(self.clock, key);
        self.clock
    }

    fn get(&mut self, key: i64) -> i64 {
        match self.map.get(&key).copied() {
            Some((val, stamp)) => {
                self.order.remove(&stamp);
                let ns = self.touch(key);
                self.map.insert(key, (val, ns));
                val
            }
            None => -1,
        }
    }

    fn put(&mut self, key: i64, val: i64) {
        if let Some(&(_, stamp)) = self.map.get(&key) {
            self.order.remove(&stamp);
        }
        let ns = self.touch(key);
        self.map.insert(key, (val, ns));
        while self.map.len() > self.cap {
            let (&oldest, &k) = self.order.iter().next().unwrap();
            self.order.remove(&oldest);
            self.map.remove(&k);
        }
    }
}

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).unwrap();
    let mut lines = input.lines();

    let cap: usize = loop {
        match lines.next() {
            Some(l) if l.trim().is_empty() => continue,
            Some(l) => break l.trim().parse().unwrap(),
            None => return,
        }
    };
    let mut cache = Lru::new(cap);

    let stdout = io::stdout();
    let mut out = io::BufWriter::new(stdout.lock());
    for line in lines {
        let mut parts = line.split_ascii_whitespace();
        match parts.next() {
            Some("get") => {
                let k: i64 = parts.next().unwrap().parse().unwrap();
                writeln!(out, "{}", cache.get(k)).unwrap();
            }
            Some("put") => {
                let k: i64 = parts.next().unwrap().parse().unwrap();
                let v: i64 = parts.next().unwrap().parse().unwrap();
                cache.put(k, v);
            }
            _ => {}
        }
    }
}
