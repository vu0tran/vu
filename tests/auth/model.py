# For run_auth.sh. "make FILE": random passwords (ASCII, Unicode, empty, long, bytes that aren't UTF-8)
# hashed as Django does (with Django itself when it's installed, else hashlib in Django's format),
# plus malformed hashes that must not match. "check": reads hashes.vu's output on stdin and checks it.
import base64, hashlib, os, random, sys

def django_encode(pw, salt, n):
    # Django itself when it's importable (the hashes Vu must accept), else the same with hashlib
    try:
        from django.conf import settings
        if not settings.configured: settings.configure(PASSWORD_HASHERS=["django.contrib.auth.hashers.PBKDF2PasswordHasher"])
        from django.contrib.auth.hashers import PBKDF2PasswordHasher
        if pw_is_utf8(pw): return PBKDF2PasswordHasher().encode(pw.decode("utf-8"), salt, n)
    except ImportError:
        pass
    return django_hash(pw, salt, n)

def django_hash(pw, salt, n):
    return "pbkdf2_sha256$%d$%s$%s" % (n, salt, base64.b64encode(hashlib.pbkdf2_hmac("sha256", pw, salt.encode(), n)).decode())

def django_check(pw, encoded):
    try:
        from django.conf import settings
        if not settings.configured: settings.configure(PASSWORD_HASHERS=["django.contrib.auth.hashers.PBKDF2PasswordHasher"])
        from django.contrib.auth.hashers import check_password
        return check_password(pw.decode("utf-8"), encoded) if pw_is_utf8(pw) else None
    except ImportError:
        return None

def pw_is_utf8(pw):
    try: pw.decode("utf-8"); return True
    except UnicodeDecodeError: return False

def passwords(rng):
    out = [b"", b"a", b"hunter2", "pässwörd 中文 😀".encode(), b"x" * 1000, b"tab\there", b"$dollar$", b"\xff\xfe bad"]
    alphabet = "abcAZ09 !$%^&*()_+-=[]{}|;:',.<>/?`~éß中😀"
    while len(out) < 60:
        out.append("".join(rng.choice(alphabet) for _ in range(rng.randint(1, 40))).encode())
    return out

rng = random.Random(int(sys.argv[3]) if len(sys.argv) > 3 else 7)
if sys.argv[1] == "make":
    with open(sys.argv[2], "w") as f:
        expect = []
        for i, pw in enumerate(passwords(rng)):
            salt = "".join(rng.choice("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(22))
            enc = django_encode(pw, salt, rng.randint(1, 3000))
            if i % 3 == 0:                      # the wrong password
                f.write("%s\t%s\n" % ((pw + b"!").hex(), enc)); expect.append(False)
            else:
                f.write("%s\t%s\n" % (pw.hex(), enc)); expect.append(True)
        bad = ["", "pbkdf2_sha256", "pbkdf2_sha256$$salt$hash", "pbkdf2_sha256$0$salt$" + django_hash(b"a", "salt", 1).split("$")[3],
               "pbkdf2_sha256$-1$salt$x", "pbkdf2_sha256$1x$salt$x", "pbkdf2_sha256$1$$" + django_hash(b"a", "", 1).split("$")[3],
               "pbkdf2_sha1$1$salt$" + django_hash(b"a", "salt", 1).split("$")[3], "PBKDF2_SHA256$1$salt$" + django_hash(b"a", "salt", 1).split("$")[3],
               "pbkdf2_sha256$1$salt$" + django_hash(b"a", "salt", 1).split("$")[3] + "$extra", "pbkdf2_sha256$99999999999$s$x",
               "pbkdf2_sha256$20000000$s$x", "bcrypt$2b$12$abc", "pbkdf2_sha256$1$salt$" + django_hash(b"a", "salt", 1).split("$")[3][:-1]]
        for b in bad:
            f.write("%s\t%s\n" % (b"a".hex(), b)); expect.append(False)
    with open(sys.argv[2] + ".want", "w") as f: f.write("\n".join(str(e).lower() for e in expect) + "\n")
else:
    lines = sys.stdin.read().split("\n")
    want = open(sys.argv[2] + ".want").read().split()
    got = [l for l in lines if l in ("true", "false")]
    bad = 0
    if got != want:
        print("FAIL  checks: got %s, want %s" % (got, want)); bad += 1
    made = [l.split("\t") for l in lines if l.startswith("V\t")]
    django_used = False
    for _, pwhex, enc in made:
        pw = bytes.fromhex(pwhex)
        parts = enc.split("$")
        if len(parts) != 4 or len(parts[2]) != 22 or not parts[2].isalnum() or django_hash(pw, parts[2], int(parts[1])) != enc:
            print("FAIL  vu's hash of %r: %s" % (pw, enc)); bad += 1
        d = django_check(pw, enc)
        if d is not None:
            django_used = True
            if not d: print("FAIL  Django rejects vu's hash of %r: %s" % (pw, enc)); bad += 1
    if len(made) != 41 or not made[-1][2].startswith("pbkdf2_sha256$600000$"):
        print("FAIL  expected 41 hashes, the last with 600000 iterations"); bad += 1
    if len(set(m[2].split("$")[2] for m in made)) != len(made):
        print("FAIL  salts repeat"); bad += 1
    rh = [l for l in lines if l.startswith("rehash ")]
    if rh != ["rehash false true true"]: print("FAIL  needs_rehash: %s" % rh); bad += 1
    print("django: %s" % ("checked with Django" if django_used else "Django not installed: checked with hashlib"))
    sys.exit(1 if bad else 0)
