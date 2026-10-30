# For run_s3.sh: starts moto's S3 (signatures checked: INITIAL_NO_AUTH_ACTION_COUNT), makes a user with
# a key and a bucket, runs live.vu (arg 1) against it, and checks its output and the presigned URLs.
import os, random, socket, subprocess, sys, time, urllib.request, urllib.error
import boto3
port = random.randint(20000, 40000)
env = dict(os.environ, INITIAL_NO_AUTH_ACTION_COUNT="4")
srv = subprocess.Popen([sys.executable, "-m", "moto.server", "-p", str(port)], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    for _ in range(200):
        try: socket.create_connection(("127.0.0.1", port), 0.2); break
        except OSError: time.sleep(0.1)
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
    port2 = random.randint(40001, 60000)
    srv2 = subprocess.Popen([sys.executable, "-m", "moto.server", "-p", str(port2)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(200):
            try: socket.create_connection(("127.0.0.1", port2), 0.2); break
            except OSError: time.sleep(0.1)
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
