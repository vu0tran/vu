use std::io::{self, Read, Write};

type Tree = Option<Box<Node>>;

struct Node {
    key: i64,
    height: u32,
    left: Tree,
    right: Tree,
}

fn height(t: &Tree) -> u32 {
    t.as_ref().map_or(0, |n| n.height)
}

fn fix(n: &mut Node) {
    n.height = 1 + height(&n.left).max(height(&n.right));
}

fn insert(t: &mut Tree, key: i64) {
    if let Some(n) = t.as_mut() {
        if key < n.key {
            insert(&mut n.left, key);
        } else if key > n.key {
            insert(&mut n.right, key);
        } else {
            return;
        }
        fix(n);
        return;
    }
    *t = Some(Box::new(Node { key, height: 1, left: None, right: None }));
}

fn min_key(n: &Node) -> i64 {
    let mut cur = n;
    while let Some(l) = cur.left.as_deref() {
        cur = l;
    }
    cur.key
}

fn delete(t: &mut Tree, key: i64) {
    let Some(n) = t.as_mut() else { return };
    if key < n.key {
        delete(&mut n.left, key);
        fix(n);
        return;
    }
    if key > n.key {
        delete(&mut n.right, key);
        fix(n);
        return;
    }
    if n.left.is_some() && n.right.is_some() {
        let m = min_key(n.right.as_deref().unwrap());
        n.key = m;
        delete(&mut n.right, m);
        fix(n);
        return;
    }
    let child = if n.left.is_some() { n.left.take() } else { n.right.take() };
    *t = child;
}

fn inorder(t: &Tree, acc: &mut Vec<i64>) {
    if let Some(n) = t {
        inorder(&n.left, acc);
        acc.push(n.key);
        inorder(&n.right, acc);
    }
}

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).unwrap();

    let stdout = io::stdout();
    let mut out = io::BufWriter::new(stdout.lock());
    let mut root: Tree = None;
    let mut keys: Vec<i64> = Vec::new();

    for line in input.lines() {
        let mut parts = line.split_ascii_whitespace();
        match parts.next() {
            Some("insert") => {
                let x: i64 = parts.next().unwrap().parse().unwrap();
                insert(&mut root, x);
            }
            Some("delete") => {
                let x: i64 = parts.next().unwrap().parse().unwrap();
                delete(&mut root, x);
            }
            Some("inorder") => {
                keys.clear();
                inorder(&root, &mut keys);
                let strs: Vec<String> = keys.iter().map(|k| k.to_string()).collect();
                writeln!(out, "{}", strs.join(" ")).unwrap();
            }
            Some("height") => {
                writeln!(out, "{}", height(&root)).unwrap();
            }
            _ => {}
        }
    }
}
