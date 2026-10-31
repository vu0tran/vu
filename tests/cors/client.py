# For run_cors.sh: Chromium loads the page from one origin; its script calls an API on another that
# allows it (with credentials and a preflight) and one that doesn't. Skipped without Playwright.
import socket, subprocess, sys, time
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("skipped: no Playwright"); sys.exit(0)
def free():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p
ports = [free(), free(), free()]
srv = subprocess.Popen([sys.argv[1]] + [str(p) for p in ports], cwd=sys.argv[2], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
try:
    for p in ports:
        for _ in range(200):
            try: socket.create_connection(("127.0.0.1", p), 0.2).close(); break
            except OSError: time.sleep(0.05)
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page()
        pg.goto("http://127.0.0.1:%d/index.html?api=%d&other=%d" % tuple(ports))
        pg.wait_for_function("document.getElementById('out').textContent.includes('done')", timeout=15000)
        got = pg.text_content("#out").strip().split("\n"); b.close()
finally:
    srv.terminate(); srv.wait(timeout=10)
want = ["get 200 null", "post got [1] with Bearer t", "other blocked", "done"]
# (x-seen isn't exposed to the page: it isn't a safelisted header and isn't in Expose-Headers)
if got != want: print("FAIL  Chromium saw %r, want %r" % (got, want)); sys.exit(1)
print("cors: Chromium called the allowed API (a preflight, credentials) and was kept from the other")
