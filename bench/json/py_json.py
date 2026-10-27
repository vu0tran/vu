# Parse a JSON file with Python's json module (C-accelerated scanner) and count nodes.
import json, sys
def count(v, n):
    if isinstance(v, list): n[4] += 1; [count(x, n) for x in v]
    elif isinstance(v, dict): n[5] += 1; [count(x, n) for x in v.values()]
    elif isinstance(v, str): n[3] += 1
    elif v is None: n[0] += 1
    elif isinstance(v, bool): n[1] += 1
    else: n[2] += 1
n = [0] * 6
count(json.load(open(sys.argv[1], encoding='utf-8')), n)
print(f"objects {n[5]}, arrays {n[4]}, strings {n[3]}, numbers {n[2]}")
