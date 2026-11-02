# Writes tools/loader.js into loader.vu as the one-line string LOADER_JS.
import os, re
d = os.path.dirname(os.path.abspath(__file__))
js = open(os.path.join(d, 'loader.js')).read().split('\n', 1)[1].strip('\n')
esc = js.replace('\\', '\\\\').replace('"', '\\"').replace('{', '{{').replace('}', '}}').replace('\n', '\\n')
p = os.path.join(d, '..', 'loader.vu')
s = open(p).read()
s = re.sub(r'const LOADER_JS = "(?:[^"\\]|\\.)*"(\n"\n)?|const LOADER_JS = "\n.*?\n"\n', lambda m: 'const LOADER_JS = "' + esc + '"\n', s, count=1, flags=re.S)
open(p, 'w').write(s)
