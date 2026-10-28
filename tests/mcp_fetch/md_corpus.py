# Not in the gate (it needs a corpus): how close html2md's Markdown comes to the reference's (Readability.js and readabilipy's Python
# extractor, each through markdownify), on real pages: word overlap (precision, recall, F1 of the
# multiset of words) and how many links each keeps. The pages: Readability's own test suite,
#   git clone --depth 1 --filter=blob:none --sparse https://github.com/mozilla/readability rd
#   (cd rd && git sparse-checkout set test/test-pages)
#   PY tests/mcp_fetch/md_corpus.py MD_DRIVER rd/test/test-pages [MAX] [-v]
# with PY a Python that has mcp-server-fetch (and readabilipy's node packages, for Readability.js),
# MD_DRIVER tests/mcp_fetch/md_driver.vu built beside a copy of mcp/fetch/*.vu.
import collections, glob, json, os, re, subprocess, sys
from mcp_server_fetch.server import extract_content_from_html
pages = sorted(glob.glob(sys.argv[2] + "/*/source.html"))[: int(sys.argv[3]) if len(sys.argv) > 3 else 1000]
htmls = [open(p, encoding="utf-8", errors="replace").read() for p in pages]
out = subprocess.run([sys.argv[1]], input="".join(json.dumps(h) + "\n" for h in htmls), capture_output=True, text=True).stdout.splitlines()
mine = [json.loads(o) for o in out]
def words(s): return collections.Counter(w.lower() for w in re.findall(r"\w+", s))
def prf(a, b):
    ca, cb = words(a), words(b)
    inter = sum((ca & cb).values())
    p = inter / max(1, sum(ca.values())); r = inter / max(1, sum(cb.values()))
    return p, r, (2 * p * r / (p + r) if p + r else 0)
rows = []
for path, h, m in zip(pages, htmls, mine):
    js = extract_content_from_html(h, True)
    py = extract_content_from_html(h, False)
    rows.append((os.path.basename(os.path.dirname(path)), prf(m, js), prf(m, py), prf(py, js), len(re.findall(r"\]\(", m)), len(re.findall(r"\]\(", js)), len(m), len(js)))
def med(xs): xs = sorted(xs); return xs[len(xs) // 2]
for name, a, b, c, lm, lj, nm, nj in rows if "-v" in sys.argv else []:
    print("%-40s vs js F1 %.2f (p %.2f r %.2f)  vs py F1 %.2f   py-vs-js F1 %.2f  links %d/%d  chars %d/%d" % (name[:40], a[2], a[0], a[1], b[2], c[2], lm, lj, nm, nj))
print("%d pages. html2md vs Readability.js: median F1 %.3f, precision %.3f, recall %.3f; vs the Python extractor: median F1 %.3f; the reference's two extractors vs each other: median F1 %.3f"
      % (len(rows), med([r[1][2] for r in rows]), med([r[1][0] for r in rows]), med([r[1][1] for r in rows]), med([r[2][2] for r in rows]), med([r[3][2] for r in rows])))
