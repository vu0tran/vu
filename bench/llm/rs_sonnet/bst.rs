use std::io::{self, BufRead, Write};

struct Node {
    key: i64,
    left: Option<Box<Node>>,
    right: Option<Box<Node>>,
}

fn insert(node: Option<Box<Node>>, key: i64) -> Option<Box<Node>> {
    match node {
        None => Some(Box::new(Node { key, left: None, right: None })),
        Some(mut n) => {
            if key < n.key {
                n.left = insert(n.left.take(), key);
            } else if key > n.key {
                n.right = insert(n.right.take(), key);
            }
            Some(n)
        }
    }
}

fn min_key(node: &Node) -> i64 {
    let mut cur = node;
    while let Some(l) = cur.left.as_deref() {
        cur = l;
    }
    cur.key
}

fn delete(node: Option<Box<Node>>, key: i64) -> Option<Box<Node>> {
    let mut n = node?;
    if key < n.key {
        n.left = delete(n.left.take(), key);
        Some(n)
    } else if key > n.key {
        n.right = delete(n.right.take(), key);
        Some(n)
    } else {
        match (n.left.take(), n.right.take()) {
            (None, None) => None,
            (Some(l), None) => Some(l),
            (None, Some(r)) => Some(r),
            (Some(l), Some(r)) => {
                let m = min_key(&r);
                n.key = m;
                n.left = Some(l);
                n.right = delete(Some(r), m);
                Some(n)
            }
        }
    }
}

fn inorder(node: &Option<Box<Node>>, out: &mut Vec<i64>) {
    if let Some(n) = node {
        inorder(&n.left, out);
        out.push(n.key);
        inorder(&n.right, out);
    }
}

fn height(node: &Option<Box<Node>>) -> usize {
    match node {
        None => 0,
        Some(n) => 1 + height(&n.left).max(height(&n.right)),
    }
}

fn main() {
    let stdin = io::stdin();
    let out = io::stdout();
    let mut out = out.lock();
    let mut root: Option<Box<Node>> = None;
    for line in stdin.lock().lines() {
        let line = line.unwrap();
        let mut parts = line.split_ascii_whitespace();
        let cmd = match parts.next() {
            Some(c) => c,
            None => continue,
        };
        match cmd {
            "insert" => {
                let x: i64 = parts.next().unwrap().parse().unwrap();
                root = insert(root.take(), x);
            }
            "delete" => {
                let x: i64 = parts.next().unwrap().parse().unwrap();
                root = delete(root.take(), x);
            }
            "inorder" => {
                let mut v = Vec::new();
                inorder(&root, &mut v);
                let s: Vec<String> = v.iter().map(|x| x.to_string()).collect();
                writeln!(out, "{}", s.join(" ")).unwrap();
            }
            "height" => {
                writeln!(out, "{}", height(&root)).unwrap();
            }
            _ => {}
        }
    }
}
