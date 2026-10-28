"""Turns the design canvas's Main.dc.html into one standalone page (index.html) and a Cloudflare Worker
that serves it (worker.js). The page's templates ({{holes}}, <sc-for>, <sc-if>) become htm templates
rendered by Preact, both bundled in.
  python3 site/build.py site/Main.dc.html site/out
Main.dc.html is the page as the design canvas keeps it (edit it there, then copy it here).
GitHub Actions runs this and deploys site/out/worker.js on every push that changes site/
(.github/workflows/site.yml)."""
import html as htmllib
import json
import os
import re
import sys

src_path, out = sys.argv[1], sys.argv[2]
here = os.path.dirname(os.path.abspath(__file__))
s = open(src_path).read()

title = re.search(r'<title>(.*?)</title>', s, re.S).group(1)
helmet = re.search(r'<helmet>(.*?)</helmet>', s, re.S).group(1)
body = s[s.index('</helmet>') + len('</helmet>'):s.index('</x-dc>')]
logic = re.search(r'<script type="text/x-dc"[^>]*>(.*?)</script>', s, re.S).group(1)

body = re.sub(r'<!--.*?-->', '', body, flags=re.S)
assert '`' not in body and '${' not in body and '\\' not in body

def expr(path):
    return path.strip()

# entities: htm doesn't decode them
body = body.replace('&#160;', ' ').replace('&lt;', "${'<'}").replace('&gt;', "${'>'}").replace('&amp;', '&')

# repeats and branches, innermost first
FOR = re.compile(r'<sc-for list="\{\{\s*([\w.$]+)\s*\}\}" as="(\w+)"[^>]*>((?:(?!<sc-for\b).)*?)</sc-for>', re.S)
IF = re.compile(r'<sc-if value="\{\{\s*([\w.$]+)\s*\}\}"[^>]*>((?:(?!<sc-if\b).)*?)</sc-if>', re.S)
while True:
    n0 = body
    body = FOR.sub(lambda m: '${(' + expr(m.group(1)) + ' || []).map((' + m.group(2) + ') => html`' + m.group(3) + '`)}', body)
    body = IF.sub(lambda m: '${' + expr(m.group(1)) + ' ? html`' + m.group(2) + '` : null}', body)
    if body == n0:
        break
assert '<sc-' not in body, 'unconverted sc- tag'

# attributes: a whole hole passes the value; holes inside text become a string
def attr(m):
    name, val = m.group(1), m.group(2)
    whole = re.fullmatch(r'\{\{\s*([\w.$]+)\s*\}\}', val)
    if whole:
        return name + '=${' + expr(whole.group(1)) + '}'
    parts = re.split(r'\{\{\s*([\w.$]+)\s*\}\}', val)
    js = ' + '.join(json.dumps(p) if i % 2 == 0 else '(' + expr(p) + ')' for i, p in enumerate(parts) if p != '' or i % 2)
    return name + '=${' + js + '}'
body = re.sub(r'([\w:-]+)="([^"]*\{\{[^"]*)"', attr, body)
# text holes
body = re.sub(r'\{\{\s*([\w.$]+)\s*\}\}', lambda m: '${' + expr(m.group(1)) + '}', body)
assert '{{' not in body

preact = open(os.path.join(here, 'vendor/preact.min.umd.js')).read()
htm = open(os.path.join(here, 'vendor/htm.umd.js')).read()
desc = "Vu: an experimental programming language for the age of AI. Memory-safe, as fast as Rust, and 21-42% fewer tokens to write."
icon = ("data:image/svg+xml," + "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' fill='%23090908'/%3E"
        "%3Ctext x='4' y='23' font-family='Georgia,serif' font-size='21' fill='%23F2EEE4'%3Evu%3C/text%3E%3Ccircle cx='27' cy='21' r='2.4' fill='%23E3BF86'/%3E%3C/svg%3E")

page = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{htmllib.escape(desc)}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{htmllib.escape(desc)}">
<meta name="theme-color" content="#090908">
<link rel="icon" href="{icon}">
{helmet.strip()}
</head>
<body>
<div id="app"></div>
<script>/* Preact 10.24.3, MIT License, (c) Jason Miller */
{preact}</script>
<script>/* htm 3.1.1, Apache License 2.0, (c) Google LLC */
{htm}</script>
<script>
var html = htm.bind(preact.h);
var DCLogic = preact.Component;
{logic.strip()}
function view(html, v) {{ with (v) {{ return html`{body.strip()}`; }} }}
Component.prototype.render = function () {{ return view(html, this.renderVals()); }};
preact.render(preact.h(Component, {{}}), document.getElementById('app'));
</script>
</body>
</html>
'''
os.makedirs(out, exist_ok=True)
open(os.path.join(out, 'index.html'), 'w').write(page)
worker = '''// Cloudflare Worker: serves the Vu landing page (one self-contained HTML file).
const PAGE = ''' + json.dumps(page) + ''';

export default {
  async fetch(request) {
    const url = new URL(request.url);
    if (url.pathname !== '/' && url.pathname !== '/index.html') {
      return new Response('Not found', { status: 404, headers: { 'content-type': 'text/plain; charset=utf-8' } });
    }
    return new Response(PAGE, {
      headers: {
        'content-type': 'text/html; charset=utf-8',
        'cache-control': 'public, max-age=300',
        'x-content-type-options': 'nosniff',
        'referrer-policy': 'strict-origin-when-cross-origin'
      }
    });
  }
};
'''
open(os.path.join(out, 'worker.js'), 'w').write(worker)
print('index.html', len(page), 'bytes; worker.js', len(worker), 'bytes')
