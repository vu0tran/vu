use std::thread;

fn a(i: usize, j: usize) -> f64 {
    1.0 / ((i + j) * (i + j + 1) / 2 + i + 1) as f64
}

fn mul(v: &[f64], out: &mut [f64], transpose: bool) {
    let threads = thread::available_parallelism().map(|n| n.get()).unwrap_or(1);
    let chunk = (out.len() + threads - 1) / threads;
    thread::scope(|s| {
        for (c, part) in out.chunks_mut(chunk).enumerate() {
            s.spawn(move || {
                for (k, o) in part.iter_mut().enumerate() {
                    let i = c * chunk + k;
                    let mut sum = 0.0;
                    for (j, vj) in v.iter().enumerate() {
                        sum += if transpose { a(j, i) } else { a(i, j) } * vj;
                    }
                    *o = sum;
                }
            });
        }
    });
}

fn main() {
    let n: usize = std::env::args().nth(1).and_then(|s| s.parse().ok()).unwrap_or(100);
    let mut u = vec![1.0; n];
    let mut v = vec![0.0; n];
    let mut tmp = vec![0.0; n];
    for _ in 0..10 {
        mul(&u, &mut tmp, false);
        mul(&tmp, &mut v, true);
        mul(&v, &mut tmp, false);
        mul(&tmp, &mut u, true);
    }
    let (mut vbv, mut vv) = (0.0, 0.0);
    for i in 0..n {
        vbv += u[i] * v[i];
        vv += v[i] * v[i];
    }
    println!("{:.9}", (vbv / vv).sqrt());
}
