# For run_s3.sh: random requests, signed by botocore (the AWS SDK for Python's signer), compared with
# what s3.vu makes. "cases FILE SEED" writes them; "check FILE" reads main.vu's output on stdin.
import datetime, random, sys
from urllib.parse import quote, urlsplit, parse_qsl

ENDPOINTS = [("https://s3.amazonaws.com", "us-east-1"), ("https://s3.eu-west-2.amazonaws.com", "eu-west-2"),
             ("https://abc123.r2.cloudflarestorage.com", "auto"), ("http://127.0.0.1:9000", "us-east-1"),
             ("https://nyc3.digitaloceanspaces.com/", "nyc3"), ("https://s3.us-east-1.amazonaws.com:443", "us-east-1")]

def cases(path, seed):
    rng = random.Random(seed)
    lines = []
    alphabet = "abcXYZ019 -_.~/!$&'()*+,;=:@%?#[]é中😀"
    for i in range(120):
        ep, region = rng.choice(ENDPOINTS)
        bucket = rng.choice(["my-bucket", "data.example", "Uploads", "b1", "logs-2026"])
        key = "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 30)))
        if i % 10 == 0: key = "a//b/./../c"
        body = bytes(rng.randrange(256) for _ in range(rng.choice([0, 1, 100, 5000])))
        ctype = rng.choice(["", "image/png", "text/plain; charset=utf-8", "application/json", "a  b   c"])
        t = rng.randint(0, 4102444800)
        lines.append("\t".join([ep, region, bucket, key.encode().hex(), rng.choice(["GET", "PUT", "DELETE", "HEAD"]), body.hex(), ctype, str(t), str(rng.choice([1, 60, 3600, 604800]))]))
    open(path, "w").write("\n".join(lines) + "\n")

def check(path):
    from botocore.auth import S3SigV4Auth, S3SigV4QueryAuth
    from botocore.awsrequest import AWSRequest
    from botocore.credentials import Credentials
    import botocore.auth
    creds = Credentials("AKIDEXAMPLE", "wJalrXUtnFEMI/K7MDENG+bPxRfiCYEXAMPLEKEY")
    got = sys.stdin.read().split("\n")
    bad = 0
    n = 0
    for line, out in zip(open(path).read().split("\n")[:-1], got):
        ep, region, bucket, keyhex, method, bodyhex, ctype, t, expires = line.split("\t")
        key = bytes.fromhex(keyhex).decode()
        body = bytes.fromhex(bodyhex)
        parts = out.split("\t")
        url = parts[0]
        # the URL: botocore encodes keys this way (percent_encode with '/~' safe)
        e = ep.rstrip("/")
        scheme, host = e.split("://")
        if scheme == "https" and host.endswith(":443"): host = host[:-4]
        virtual = ".amazonaws.com" in host and all(c.islower() or c.isdigit() or c == "-" for c in bucket) and 3 <= len(bucket) <= 63
        want_url = "%s://%s.%s/%s" % (scheme, bucket, host, quote(key, safe="/~")) if virtual else "%s://%s/%s/%s" % (scheme, host, quote(bucket, safe="~"), quote(key, safe="/~"))
        when = datetime.datetime.fromtimestamp(int(t), datetime.timezone.utc).replace(tzinfo=None)
        botocore.auth.get_current_datetime = lambda: when
        headers = {"content-type": ctype} if ctype else {}
        req = AWSRequest(method=method, url=want_url, data=body, headers=headers)
        S3SigV4Auth(creds, "s3", region).add_auth(req)
        want = {"x-amz-date": req.headers["X-Amz-Date"], "x-amz-content-sha256": req.headers["X-Amz-Content-SHA256"], "authorization": req.headers["Authorization"]}
        mine = {}
        for h in parts[1:-1]:
            k, _, v = h.partition(": ")
            mine[k.lower()] = v
        q = AWSRequest(method=method, url=want_url)
        S3SigV4QueryAuth(creds, "s3", region, expires=int(expires)).add_auth(q)
        pw, pm = urlsplit(q.url), urlsplit(parts[-1])
        same_presign = (pw.scheme, pw.netloc, pw.path) == (pm.scheme, pm.netloc, pm.path) and sorted(parse_qsl(pw.query)) == sorted(parse_qsl(pm.query))
        n += 1
        if url != want_url or any(mine.get(k) != v for k, v in want.items()) or not same_presign:
            bad += 1
            if bad <= 5:
                print("FAIL  %s %r in %s (%s)" % (method, key, bucket, ep))
                if url != want_url: print("      url %s, want %s" % (url, want_url))
                for k, v in want.items():
                    if mine.get(k) != v: print("      %s: %s, want %s" % (k, mine.get(k), v))
                if not same_presign: print("      presigned %s\n      want      %s" % (parts[-1], q.url))
    print("%d requests signed as botocore signs them, %d not" % (n - bad, bad))
    sys.exit(1 if bad or n != 120 else 0)

if sys.argv[1] == "cases": cases(sys.argv[2], int(sys.argv[3]))
else: check(sys.argv[2])
