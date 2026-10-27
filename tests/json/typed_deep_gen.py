# Input for json/typed_deep.vu: a recursive type nested 300 and 400 levels (3 JSON levels each),
# and a skipped field nested 999 and 200000 levels.
import sys
def br(n): return '{"Br":{"kids":[' * n + '"Leaf"' + ']}}' * n
open(sys.argv[1], 'w').write('\n'.join([br(300), br(400), '{"a":1,"z":' + '[' * 999 + ']' * 999 + '}',
                                        '{"a":1,"z":' + '[' * 200000 + ']' * 200000 + '}']))
