import os,sys,shutil,subprocess,importlib.util
here=os.path.dirname(os.path.abspath(__file__))
spec=importlib.util.spec_from_file_location("cases",os.path.join(here,os.environ.get("CASES","cases.py"))); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
out=sys.argv[1]; refdir=sys.argv[2]
KNIP=os.environ.get("KNIP", "knip.js")  # path to knip/bin/knip.js of an npm install of knip
os.makedirs(refdir,exist_ok=True)
names=sys.argv[3:] or list(m.CASES)
for name in names:
    d=os.path.join(out,name)
    shutil.rmtree(d,ignore_errors=True)
    for p,c in m.CASES[name].items():
        f=os.path.join(d,p); os.makedirs(os.path.dirname(f),exist_ok=True); open(f,"w").write(c)
    subprocess.run(["git","init","-q"],cwd=d)
    r=subprocess.run(["node",KNIP],cwd=d,capture_output=True,text=True)
    open(os.path.join(refdir,name+".txt"),"w").write(r.stdout)
    print(name, r.returncode, len(r.stdout.splitlines()), r.stderr.strip()[:200])
