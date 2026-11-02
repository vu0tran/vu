import sys, os, collections, json
import yaml, tomllib
W = os.path.dirname(os.path.abspath(__file__))
cnt = collections.Counter(); ver = collections.Counter(); feats = collections.Counter(); n = 0
std = {"errcheck","govet","ineffassign","staticcheck","unused"}
alias = {"gosimple":"staticcheck","stylecheck":"staticcheck","vet":"govet","vetshadow":"govet"}
for f in sorted(os.listdir(W + "/cfg")):
    p = W + "/cfg/" + f
    try:
        if f.endswith(".toml"): c = tomllib.load(open(p, "rb"))
        elif f.endswith(".json"): c = json.load(open(p))
        else: c = yaml.safe_load(open(p))
    except Exception as e:
        feats["parse-error"] += 1; continue
    if not isinstance(c, dict): continue
    n += 1
    v = str(c.get("version", "1")); ver[v] += 1
    L = c.get("linters") or {}
    en = set()
    if v == "2":
        d = L.get("default", "standard")
        feats["default:" + d] += 1
        if d == "standard": en |= std
        if d == "all": en |= {"ALL"}
    else:
        if L.get("disable-all"): feats["v1:disable-all"] += 1
        elif L.get("enable-all"): en |= {"ALL"}; feats["v1:enable-all"] += 1
        else: en |= std
    for x in L.get("enable") or []: en.add(alias.get(x, x))
    for x in L.get("disable") or []: en.discard(alias.get(x, x))
    F = c.get("formatters") or {}
    for x in F.get("enable") or []: en.add(x)
    for x in en: cnt[x] += 1
    for k in ("run", "output", "issues", "severity"):
        for kk in (c.get(k) or {}): feats[k + "." + kk] += 1
    ex = (L.get("exclusions") or {})
    for kk in ex: feats["linters.exclusions." + kk] += 1
    for kk in (L.get("settings") or c.get("linters-settings") or {}): feats["settings." + kk] += 1
print("configs", n, dict(ver))
for k, c in cnt.most_common(60): print(f"{c:4} {k}")
print("--- features")
for k, c in feats.most_common(70): print(f"{c:4} {k}")
