use std::io::{self, Read, Write};

struct Node {
    key: i64,
    left: Link,
    right: Link,
}

type Link = Option<Box<Node>>;

fn insert(link: &mut Link, key: i64) {
    match link {
        Some(node) => {
            if key < node.key {
                insert(&mut node.left, key);
            } else if key > node.key {
                insert(&mut node.right, key);
            }
        }
        None => *link = Some(Box::new(Node { key, left: None, right: None })),
    }
}

/// Removes the smallest key of a non-empty subtree and returns it.
fn take_min(link: &mut Link) -> i64 {
    if link.as_ref().unwrap().left.is_some() {
        take_min(&mut link.as_mut().unwrap().left)
    } else {
        let Node { key, right, .. } = *link.take().unwrap();
        *link = right;
        key
    }
}

fn delete(link: &mut Link, key: i64) {
    let Some(node) = link else { return };
    if key < node.key {
        delete(&mut node.left, key);
    } else if key > node.key {
        delete(&mut node.right, key);
    } else if node.left.is_some() && node.right.is_some() {
        node.key = take_min(&mut node.right);
    } else {
        let child = if node.left.is_some() {
            node.left.take()
        } else {
            node.right.take()
        };
        *link = child;
    }
}

fn height(link: &Link) -> usize {
    match link {
        None => 0,
        Some(node) => 1 + height(&node.left).max(height(&node.right)),
    }
}

fn inorder(link: &Link, keys: &mut Vec<i64>) {
    if let Some(node) = link {
        inorder(&node.left, keys);
        keys.push(node.key);
        inorder(&node.right, keys);
    }
}

fn run() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).expect("read stdin");
    let stdout = io::stdout();
    let mut out = io::BufWriter::new(stdout.lock());

    let mut root: Link = None;
    for line in input.lines() {
        let mut parts = line.split_whitespace();
        let Some(cmd) = parts.next() else { continue };
        match cmd {
            "insert" => {
                let x: i64 = parts.next().unwrap().parse().unwrap();
                insert(&mut root, x);
            }
            "delete" => {
                let x: i64 = parts.next().unwrap().parse().unwrap();
                delete(&mut root, x);
            }
            "inorder" => {
                let mut keys = Vec::new();
                inorder(&root, &mut keys);
                let text: Vec<String> = keys.iter().map(|k| k.to_string()).collect();
                writeln!(out, "{}", text.join(" ")).unwrap();
            }
            "height" => writeln!(out, "{}", height(&root)).unwrap(),
            _ => {}
        }
    }
}

fn main() {
    // Deep unbalanced trees recurse deeply, so run on a thread with a large stack.
    let worker = std::thread::Builder::new()
        .stack_size(256 << 20)
        .spawn(run)
        .expect("spawn worker");
    worker.join().expect("worker panicked");
}
