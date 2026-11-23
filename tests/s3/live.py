# For run_s3.sh: starts moto's S3 (signatures checked: INITIAL_NO_AUTH_ACTION_COUNT), makes a user with
# a key and a bucket, runs live.vu (arg 1) against it, and checks its output and the presigned URLs.
import os, random, socket, subprocess, sys, time, urllib.request, urllib.error
import boto3

def ready(port, proc):
    # the socket accepts before the app behind it answers: wait for an answer (up to 60 s, on a busy
    # machine); False if the server exited first (its port taken, say) or never answered
    end = time.time() + 60
    while time.time() < end:
        if proc.poll() is not None: return False
        try:
            urllib.request.urlopen("http://127.0.0.1:%d/moto-api/" % port, timeout=2).read()
            return True
        except Exception:
            time.sleep(0.1)
    return False

def start(lo, hi, env=None):
    # a moto server on a free port in [lo, hi]: started again on another one when it doesn't come up
    for _ in range(4):
        port = random.randint(lo, hi)
        proc = subprocess.Popen([sys.executable, "-m", "moto.server", "-p", str(port)], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if ready(port, proc): return port, proc
        proc.kill(); proc.wait()
    raise SystemExit("moto didn't start (4 ports tried in %d-%d)" % (lo, hi))

env = dict(os.environ, INITIAL_NO_AUTH_ACTION_COUNT="4")
port, srv = start(20000, 40000, env)
try:
    ep = "http://127.0.0.1:%d" % port
    iam = boto3.client("iam", endpoint_url=ep, region_name="us-east-1", aws_access_key_id="x", aws_secret_access_key="y")
    iam.create_user(UserName="app")
    iam.put_user_policy(UserName="app", PolicyName="s3", PolicyDocument='{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": "s3:*", "Resource": "*"}]}')
    k = iam.create_access_key(UserName="app")["AccessKey"]
    s3 = boto3.client("s3", endpoint_url=ep, region_name="us-east-1", aws_access_key_id=k["AccessKeyId"], aws_secret_access_key=k["SecretAccessKey"])
    s3.create_bucket(Bucket="vu-test")
    r = subprocess.run([sys.argv[1], ep, k["AccessKeyId"], k["SecretAccessKey"]], capture_output=True, text=True, timeout=120)
    lines = r.stdout.split("\n")
    want = ["put ok"] * 4 + ["get true"] * 4 + ["exists true", "delete ok", "get after delete NotFound dir/with space/ünïcödé 中.bin", "exists after delete false", "wrong secret: denied"]
    bad = []
    if r.returncode != 0: bad.append("exit %d: %s" % (r.returncode, r.stderr[-500:]))
    if lines[:len(want)] != want: bad.append("got %r" % lines[:len(want)])
    get_url, put_url = lines[len(want):len(want) + 2]
    # moto answers 500 to any presigned URL while it checks signatures (boto3's own too), so the
    # presigned URLs are checked for where they lead on a second server that doesn't (their signatures
    # are checked against botocore's in model.py)
    port2, srv2 = start(40001, 60000)
    try:
        ep2 = "http://127.0.0.1:%d" % port2
        open_s3 = boto3.client("s3", endpoint_url=ep2, region_name="us-east-1", aws_access_key_id="x", aws_secret_access_key="y")
        open_s3.create_bucket(Bucket="vu-test")
        open_s3.put_object(Bucket="vu-test", Key="odd !$&'()*+,;=:@ key", Body=b"the object")
        body = urllib.request.urlopen(get_url.replace(ep, ep2)).read()
        if body != b"the object": bad.append("presigned GET gave %r" % body[:40])
        urllib.request.urlopen(urllib.request.Request(put_url.replace(ep, ep2), data=b"from a browser", method="PUT", headers={"Content-Type": "text/plain"})).read()   # (urllib's default form type makes moto drop the body)
        got = open_s3.get_object(Bucket="vu-test", Key="uploaded by url é.txt")["Body"].read()
        if got != b"from a browser": bad.append("presigned PUT stored %r" % got)
    finally:
        srv2.kill()
    names = sorted(o["Key"] for o in s3.list_objects_v2(Bucket="vu-test")["Contents"])
    if names != sorted(["plain.txt", "odd !$&'()*+,;=:@ key", "a/b/c.json"]): bad.append("keys stored: %r" % names)
    for b in bad: print("FAIL  " + b)
    print("moto: %s" % ("put, get, exists, delete and a wrong secret as expected; presigned URLs lead to the objects" if not bad else "%d problems" % len(bad)))
    sys.exit(1 if bad else 0)
finally:
    srv.kill()
