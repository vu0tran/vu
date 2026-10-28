#!/bin/sh
# mcp/vu (Vu's checker as an MCP server): a clean program, a compile error, an error in a second
# module, file names that try to leave the folder, and the docs.
d="$(cd "$(dirname "$0")" && pwd)"
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
"$d/../vu" build "$d/../mcp/vu/main.vu" -o "$work/mcp-vu" || exit 1
printf '%s\n' \
'{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"vu_check","arguments":{"source":"fn main():\n  print(\"hi\")\n"}}}' \
'{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"vu_check","arguments":{"source":"fn main():\n  let x = 1\n  x = 2\n"}}}' \
'{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"vu_check","arguments":{"files":{"main.vu":"import geo\nfn main():\n  print(\"{geo.sq(3)}\")\n","geo.vu":"fn sq(x: Int) -> Int:\n  return x * y\n"}}}}' \
'{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"vu_check","arguments":{"files":{"../x.vu":"a"}}}}' \
'{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{"name":"vu_docs","arguments":{}}}' | "$work/mcp-vu" --vu "$d/../vu" > "$work/out"
pass=0; fail=0
want() { if sed -n "$1p" "$work/out" | grep -qF "$2"; then pass=$((pass+1)); else fail=$((fail+1)); echo "FAIL answer $1: wanted $2, got $(sed -n "$1p" "$work/out" | cut -c1-300)"; fi; }
want 1 '"ok":true'
want 2 "main.vu:3: error: 'x' can't be modified"
want 3 "geo.vu:2: error: unknown name 'y'"
want 4 '"isError":true'
want 5 'This file is the'
echo "$pass passed, $fail failed"
[ $fail -eq 0 ]
