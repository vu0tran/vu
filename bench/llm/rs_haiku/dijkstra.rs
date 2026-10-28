use std::cmp::Reverse;
use std::collections::BinaryHeap;
use std::io::{self, Read, Write};

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).expect("read stdin");
    let mut nums = input
        .split_ascii_whitespace()
        .map(|t| t.parse::<u64>().expect("integer"));

    let n = nums.next().unwrap() as usize;
    let m = nums.next().unwrap() as usize;
    let s = nums.next().unwrap() as usize;

    let mut adj: Vec<Vec<(usize, u64)>> = vec![Vec::new(); n];
    for _ in 0..m {
        let u = nums.next().unwrap() as usize;
        let v = nums.next().unwrap() as usize;
        let w = nums.next().unwrap();
        adj[u].push((v, w));
    }

    let mut best = vec![u64::MAX; n];
    let mut heap = BinaryHeap::new();
    best[s] = 0;
    heap.push(Reverse((0u64, s)));
    while let Some(Reverse((d, u))) = heap.pop() {
        if d > best[u] {
            continue;
        }
        for &(v, w) in &adj[u] {
            let nd = d + w;
            if nd < best[v] {
                best[v] = nd;
                heap.push(Reverse((nd, v)));
            }
        }
    }

    let stdout = io::stdout();
    let mut out = io::BufWriter::new(stdout.lock());
    for &d in &best {
        if d == u64::MAX {
            writeln!(out, "unreachable").unwrap();
        } else {
            writeln!(out, "{}", d).unwrap();
        }
    }
}
