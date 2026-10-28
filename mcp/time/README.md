# mcp-time

The MCP time server in Vu: `get_current_time` and `convert_time` over IANA time zones, answering as
the reference server (`mcp-server-time` 2026.10.28, Python) does: the same tools, schemas, results
and error messages.

```
./vu build mcp/time/main.vu -o mcp-time
./mcp-time --local-timezone America/New_York     # or it finds the local zone as tzlocal does: $TZ, /etc/localtime
```

## What it can reach

`main` holds `Fs` and `Os` and uses them only at startup: to open the tz database
(`/usr/share/zoneinfo`, or `$TZDIR`) as a `dir.Dir`, to find the local zone, and to make a closure
that reads the clock. The tools receive those three and nothing else, so they can't read any other
file, open a connection, start a program or read the environment.

## Measured

2-vCPU Linux VM, Python 3.13 (`mcp/bench_start.py`: median of 15 starts, then 1,000
`convert_time` calls):

| | Vu | Python reference |
|---|---|---|
| install | one 197 KB binary | a 60 MB virtualenv |
| start to the `initialize` answer | 1.8 ms | 683 ms |
| memory (RSS) | 1.9 MB | 69 MB |
| `convert_time` calls per second | 12,212 | 773 |

## Checked

`tests/run_mcp_time.sh` asks both servers the same questions: `get_current_time` in every zone of the
system's tz database (447 here), then random `convert_time` requests (zones, valid and malformed
times, missing arguments, paths instead of zone names), and compares every answer as JSON (the
seconds of the current time excepted, since the clock ticks between the two). 13,840 answers on four
seeds, all the same.

## Where it differs

- **Zones the system doesn't have.** The reference falls back to Python's bundled `tzdata` for names
  the system's database lacks (old aliases such as `Africa/Asmera`); this server reads only the
  system's database, so those are "No time zone found".
- A zone whose file is an absolute symlink out of the tz folder (`localtime` on some systems) is
  refused, because the `Dir` stays inside its folder.
