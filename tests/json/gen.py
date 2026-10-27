# Random JSON corpus: writes FILE (varied spacing and escaping) and FILE.expect (compact, by Python).
# usage: gen.py COUNT SEED FILE
import json, random, sys
random.seed(int(sys.argv[2]))
def rstr():
    pool = 'abcxyz 0129"\\/\n\t\r\x01é漢😀'
    return ''.join(random.choice(pool) for _ in range(random.randint(0, 12)))
def num():
    r = random.random()
    if r < 0.4: return random.randint(-10**6, 10**6)
    if r < 0.6: return random.randint(-10**14, 10**14)
    if r < 0.8: return round(random.uniform(-1000, 1000), random.randint(1, 6))
    return random.uniform(-1, 1) * 10 ** random.randint(-30, 30)
def val(d):
    r = random.random()
    if d > 6 or r < 0.5:
        return random.choice([None, True, False, num(), num(), rstr(), rstr()])
    if r < 0.75:
        return [val(d + 1) for _ in range(random.randint(0, 6))]
    return {rstr(): val(d + 1) for _ in range(random.randint(0, 6))}
doc = [val(0) for _ in range(int(sys.argv[1]))]
open(sys.argv[3], 'w').write(json.dumps(doc, ensure_ascii=random.random() < 0.5, indent=random.choice([None, 2])))
open(sys.argv[3] + '.expect', 'w').write(json.dumps(doc, separators=(',', ':'), ensure_ascii=False) + '\n')
