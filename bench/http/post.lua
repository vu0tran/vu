-- wrk script for the JSON benchmark: every request POSTs order.json to /order.
local f = io.open(os.getenv("ORDER") or "order.json", "rb")
wrk.method = "POST"
wrk.path = "/order"
wrk.body = f:read("*a")
f:close()
wrk.headers["Content-Type"] = "application/json"
