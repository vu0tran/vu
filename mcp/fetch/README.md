# mcp-fetch

The MCP fetch server in Vu: a `fetch` tool and a `fetch` prompt that get a URL and hand a model its
text (a web page as Markdown), answering as the reference server (`mcp-server-fetch` 2026.10.28,
Python) does: the same tool and prompt, the same argument checks and messages, robots.txt read the
way it reads it, the same refusal of private addresses, redirects, text decoding, pagination and
errors. The Markdown of an HTML page is the one part that is its own (below).

```
./vu build mcp/fetch/main.vu -o mcp-fetch
./mcp-fetch                         # [--user-agent UA] [--ignore-robots-txt] [--allow-private-ips]
```

In a client's configuration it's the same entry as the reference with the command swapped:
`{"command": "/path/to/mcp-fetch", "args": []}`.

## What it can reach

`main` takes `Net` and nothing else, so the server can't read or write a file, start a program or
read the environment, whatever a page or a model sends it; the compiler refuses code that tries.
Without `--allow-private-ips` every request, redirect hops and robots.txt requests included, must
go to public addresses (Python 3.13's tables of special-purpose ranges, as the reference uses): not
the machine itself, the local network, link-local addresses (cloud metadata) or the other reserved
ranges, by any spelling (`0x7f.1`, `2130706433`, `[::ffff:127.0.0.1]`). The addresses it checks are
the ones it connects to; the reference looks the name up a second time to connect, so a name that
answers differently the second time gets past its check.

## Measured

2-vCPU Linux VM, Python 3.13, a local HTTP server; `mcp/bench_start.py` (median of 15 starts, then
1,000 `fetch` calls, each also asking for robots.txt), and for Readability.js 20 calls:

| | Vu | Python reference |
|---|---|---|
| install | one 835 KB binary | a virtualenv (109 MB here, with mcp-server-time), and Node for Readability.js |
| start to the `initialize` answer | 3.6–4.6 ms | 715–730 ms |
| memory (RSS) | 5.0 MB | 83 MB |
| a 16-byte text file | 1,020 calls/s | 49 calls/s |
| an HTML page (the V8 blog post from Readability's tests) | 107 calls/s (9 ms) | 8 calls/s with `--no-readability-js`; 881 ms a call with Readability.js |

## Checked

`tests/run_mcp_fetch.sh` (in the gate) first checks the parts that must answer exactly as the
reference's own libraries do, each on 6,000 generated inputs: URLs against pydantic's `AnyUrl`
(parsing, the rewritten text, the error), robots.txt against Protego, the address guard against the
reference's `_is_public_address`, the HTML tokenizer against Python's `html.parser`, and text
decoding against the reference's `decode_page` (httpx's `response.text` and its `<meta>` charset
sniffing). Then it runs both servers on the same requests to a local HTTP server, plain and with
AddressSanitizer: random pages (text, JSON, HTML in several charsets, gzip, chunked), redirects
(relative, scheme-relative, to other origins, past the limit of 20, to `ftp:` and `mailto:`),
random robots.txt files and statuses (401, 403, 404, 5xx, one that never arrives), status pages,
servers that hang up or cut a body short, random arguments (valid and not), the prompt, and the
guard without `--allow-private-ips`. Every answer is compared as JSON, except the Markdown of HTML
pages, whose words are compared (median word F1 0.98–0.99 on these pages).

## Where it differs

- **The Markdown of an HTML page.** The reference simplifies a page with Readability.js under Node
  when Node is installed (and installs its npm packages the first time), and with readabilipy's
  pure-Python extractor otherwise, then writes Markdown with markdownify. This server keeps the
  page's `<article>` or `<main>` (else its body) without navigation, sidebars, footers, forms,
  scripts and hidden parts (and shows hidden content that holds most of the page, as the reference
  does), and writes it as markdownify does. On the 130 real pages of Readability's own test suite
  its words agree with the reference's Readability.js output at a median F1 of 0.98 (precision
  0.98, recall 1.00); the reference's two extractors agree with each other at 0.84. It keeps more
  than Readability.js on a few pages full of links (webmd, yahoo-4, youth).
- **No proxy.** `--proxy-url` is refused, and `HTTP_PROXY`/`HTTPS_PROXY` aren't read: the server
  connects directly (it can't read the environment).
- **Charsets.** Every single-byte codec Python has, UTF-8, UTF-16 and UTF-32 decode as Python
  decodes them; the multi-byte Asian codecs (Shift_JIS, EUC-JP, GBK, GB18030, Big5, EUC-KR,
  ISO-2022-*), UTF-7 and HZ read as UTF-8 instead.
- **International host names** are mapped from a table made by asking pydantic about every code
  point in the middle of a label (`tools/gen_idna.py`), then NFC; the rules that depend on the
  neighbours (bidirectional text, joiners) beyond that aren't checked.
- **Some error texts**: a TLS failure, a malformed `Location` header or a malformed response gives
  an httpx-like message, not httpx's exact one. Bodies are limited to 64 MB, before and after
  gzip (the reference has no limit, so a small gzip body can unpack into gigabytes there).
- Argument errors show values as Python's `repr` does, with an approximation of
  `str.isprintable()` (it doesn't know which code points are unassigned), and integers beyond 64
  bits read as floats.
- Requests are answered one at a time, in order.
- The HTML tokenizer follows Python 3.13.17's `html.parser`; older Pythons tokenize some broken
  markup differently, so a reference on another Python can sniff a different `<meta>` charset.
