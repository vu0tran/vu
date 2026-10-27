fn main() {
    let n: usize = std::env::args().nth(1).and_then(|s| s.parse().ok()).unwrap_or(7);
    let mut perm1: Vec<usize> = (0..n).collect();
    let mut perm = vec![0; n];
    let mut count = vec![0; n];
    let (mut max_flips, mut checksum, mut perm_count, mut r) = (0i64, 0i64, 0i64, n);
    loop {
        while r != 1 {
            count[r - 1] = r;
            r -= 1;
        }
        perm.copy_from_slice(&perm1);
        let mut flips = 0;
        while perm[0] != 0 {
            let k = perm[0];
            perm[..=k].reverse();
            flips += 1;
        }
        max_flips = max_flips.max(flips);
        checksum += if perm_count % 2 == 0 { flips } else { -flips };
        loop {
            if r == n {
                println!("{}\nPfannkuchen({}) = {}", checksum, n, max_flips);
                return;
            }
            perm1[..=r].rotate_left(1);
            count[r] -= 1;
            if count[r] > 0 {
                break;
            }
            r += 1;
        }
        perm_count += 1;
    }
}
