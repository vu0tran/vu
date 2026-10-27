// zlib-format decompression with flate2's pure-Rust backend (miniz_oxide), N times: zb FILE.z N.
use std::io::Read;
fn main() {
    let a: Vec<String> = std::env::args().collect();
    let data = std::fs::read(&a[1]).unwrap();
    let n: usize = a[2].parse().unwrap();
    let mut out = Vec::new();
    for _ in 0..n {
        out = Vec::new();   // a new result each time, as in the others
        flate2::read::ZlibDecoder::new(&data[..]).read_to_end(&mut out).unwrap();
    }
    println!("{} {}", out.len(), crc32fast::hash(&out));
}
