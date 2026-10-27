// Parse a JSON file into a generic tree (serde_json::Value, insertion-ordered maps like Vu's) and count nodes.
use serde_json::Value;
fn count(v: &Value, n: &mut [u64; 6]) {
    match v {
        Value::Null => n[0] += 1,
        Value::Bool(_) => n[1] += 1,
        Value::Number(_) => n[2] += 1,
        Value::String(_) => n[3] += 1,
        Value::Array(a) => { n[4] += 1; for x in a { count(x, n) } }
        Value::Object(o) => { n[5] += 1; for x in o.values() { count(x, n) } }
    }
}
fn main() {
    let path = std::env::args().nth(1).unwrap();
    let src = std::fs::read_to_string(&path).unwrap();
    let v: Value = serde_json::from_str(&src).unwrap();
    let mut n = [0u64; 6];
    count(&v, &mut n);
    println!("objects {}, arrays {}, strings {}, numbers {}", n[5], n[4], n[3], n[2]);
}
