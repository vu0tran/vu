use std::thread;

fn inside(cr: f64, ci: f64) -> bool {
    let (mut zr, mut zi, mut tr, mut ti) = (0.0f64, 0.0f64, 0.0f64, 0.0f64);
    for _ in 0..10 {
        for _ in 0..5 {
            zi = (zr + zr) * zi + ci;
            zr = tr - ti + cr;
            tr = zr * zr;
            ti = zi * zi;
        }
        if tr + ti > 4.0 {
            return false;
        }
    }
    true
}

fn main() {
    let n: usize = std::env::args().nth(1).and_then(|s| s.parse().ok()).unwrap_or(200);
    let size = (n + 7) / 8 * 8;
    let row = size / 8;
    let inv = 2.0 / size as f64;
    println!("P4\n{} {}", size, size);
    let mut px = vec![0u8; size * row];
    let threads = thread::available_parallelism().map(|n| n.get()).unwrap_or(1);
    // Interleave rows across threads so each gets a similar share of the expensive ones.
    let mut work: Vec<Vec<(usize, &mut [u8])>> = (0..threads).map(|_| Vec::new()).collect();
    for (y, r) in px.chunks_mut(row).enumerate() {
        work[y % threads].push((y, r));
    }
    thread::scope(|s| {
        for rows in work {
            s.spawn(move || {
                for (y, r) in rows {
                    let ci = y as f64 * inv - 1.0;
                    for x in 0..row {
                        let mut byte = 0u8;
                        for bit in 0..8 {
                            if inside((x * 8 + bit) as f64 * inv - 1.5, ci) {
                                byte |= 0x80 >> bit;
                            }
                        }
                        r[x] = byte;
                    }
                }
            });
        }
    });
    println!("{:x}", md5::compute(&px));
}
