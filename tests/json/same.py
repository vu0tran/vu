# Exit 0 if two JSON files hold exactly the same values (floats compared exactly, key order included).
import json, math, sys
def eq(a, b):
    if isinstance(a, bool) or isinstance(b, bool): return a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b or (isinstance(a, float) and isinstance(b, float) and math.isnan(a) and math.isnan(b))
    if isinstance(a, list): return isinstance(b, list) and len(a) == len(b) and all(map(eq, a, b))
    if isinstance(a, dict):
        return isinstance(b, dict) and list(a) == list(b) and all(eq(a[k], b[k]) for k in a)
    return a == b
a = json.loads(open(sys.argv[1], encoding='utf-8').read()); b = json.loads(open(sys.argv[2], encoding='utf-8').read())
sys.exit(0 if eq(a, b) else 1)
