use std::cmp::Reverse;
use std::collections::BinaryHeap;
use std::io::{self, Read, Write};

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).unwrap();
    let mut it = input.split_ascii_whitespace().map(|t| t.parse::<i64>().unwrap());
    let n = it.next().unwrap() as usize;
    let m = it.next().unwrap() as usize;
    let s = it.next().unwrap() as usize;
    let mut adj: Vec<Vec<(usize, i64)>> = vec![Vec::new(); n];
    for _ in 0..m {
        let u = it.next().unwrap() as usize;
        let v = it.next().unwrap() as usize;
        let w = it.next().unwrap();
        adj[u].push((v, w));
    }
    let mut dist: Vec<Option<i64>> = vec![None; n];
    let mut heap = BinaryHeap::new();
    dist[s] = Some(0);
    heap.push(Reverse((0i64, s)));
    while let Some(Reverse((d, u))) = heap.pop() {
        if dist[u] != Some(d) {
            continue;
        }
        for &(v, w) in &adj[u] {
            let nd = d + w;
            if dist[v].map_or(true, |cur| nd < cur) {
                dist[v] = Some(nd);
                heap.push(Reverse((nd, v)));
            }
        }
    }
    let out = io::stdout();
    let mut out = out.lock();
    for d in dist {
        match d {
            Some(x) => writeln!(out, "{}", x).unwrap(),
            None => writeln!(out, "unreachable").unwrap(),
        }
    }
}
