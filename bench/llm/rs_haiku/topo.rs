use std::cmp::Reverse;
use std::collections::BinaryHeap;
use std::io::{self, Read, Write};

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).expect("read stdin");
    let mut nums = input
        .split_ascii_whitespace()
        .map(|t| t.parse::<usize>().expect("integer"));

    let n = nums.next().unwrap();
    let m = nums.next().unwrap();

    let mut adj: Vec<Vec<usize>> = vec![Vec::new(); n];
    let mut indegree = vec![0usize; n];
    for _ in 0..m {
        let a = nums.next().unwrap();
        let b = nums.next().unwrap();
        adj[a].push(b);
        indegree[b] += 1;
    }

    // Kahn's algorithm, always taking the smallest-numbered available task.
    let mut ready: BinaryHeap<Reverse<usize>> = (0..n)
        .filter(|&i| indegree[i] == 0)
        .map(Reverse)
        .collect();
    let mut order: Vec<usize> = Vec::with_capacity(n);
    while let Some(Reverse(u)) = ready.pop() {
        order.push(u);
        for &v in &adj[u] {
            indegree[v] -= 1;
            if indegree[v] == 0 {
                ready.push(Reverse(v));
            }
        }
    }

    let stdout = io::stdout();
    let mut out = io::BufWriter::new(stdout.lock());
    if order.len() < n {
        writeln!(out, "cycle").unwrap();
    } else {
        let text: Vec<String> = order.iter().map(|x| x.to_string()).collect();
        writeln!(out, "{}", text.join(" ")).unwrap();
    }
}
