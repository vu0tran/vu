-- 90% follow a link (GET /code: an UPDATE ... RETURNING), 10% create one (POST /links: an INSERT).
-- The codes to follow are read from codes.txt (one per line), made before the run.
local codes = {}
for line in io.lines(os.getenv("CODES") or "codes.txt") do codes[#codes + 1] = line end
local n = 0
request = function()
  n = n + 1
  if n % 10 == 0 then
    return wrk.format("POST", "/links", {["Content-Type"] = "application/json"},
                      '{"url": "https://example.com/page/' .. n .. '"}')
  end
  return wrk.format("GET", "/" .. codes[math.random(#codes)])
end
local bad = 0
response = function(status, headers, body)
  if status ~= 302 and status ~= 201 then bad = bad + 1 end
end
done = function(summary, latency, requests)
  io.write(string.format("RESULT rps=%.0f p50_ms=%.2f p99_ms=%.2f requests=%d errors=%d non2xx3xx=%d\n",
    summary.requests / (summary.duration / 1e6), latency:percentile(50) / 1000, latency:percentile(99) / 1000,
    summary.requests, summary.errors.connect + summary.errors.read + summary.errors.write + summary.errors.timeout, bad))
end
