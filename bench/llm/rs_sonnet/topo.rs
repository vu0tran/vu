use std::cmp::Reverse;
use std::collections::BinaryHeap;
use std::io::{self, Read, Write};

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).unwrap();
    let mut it = input.split_ascii_whitespace().map(|t| t.parse::<usize>().unwrap());
    let n = it.next().unwrap();
    let m = it.next().unwrap();
    let mut adj: Vec<Vec<usize>> = vec![Vec::new(); n];
    let mut indeg = vec![0usize; n];
    for _ in 0..m {
        let a = it.next().unwrap();
        let b = it.next().unwrap();
        adj[a].push(b);
        indeg[b] += 1;
    }
    let mut heap = BinaryHeap::new();
    for i in 0..n {
        if indeg[i] == 0 {
            heap.push(Reverse(i));
        }
    }
    let mut order: Vec<usize> = Vec::with_capacity(n);
    while let Some(Reverse(u)) = heap.pop() {
        order.push(u);
        for &v in &adj[u] {
            indeg[v] -= 1;
            if indeg[v] == 0 {
                heap.push(Reverse(v));
            }
        }
    }
    let out = io::stdout();
    let mut out = out.lock();
    if order.len() < n {
        writeln!(out, "cycle").unwrap();
    } else {
        let s: Vec<String> = order.iter().map(|x| x.to_string()).collect();
        writeln!(out, "{}", s.join(" ")).unwrap();
    }
}
