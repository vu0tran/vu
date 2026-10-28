"""The compiler built for WebAssembly (tools/wasm.sh) against the native one: `check` and `fmt` on
every file given must give the same exit status, the same messages and the same formatted file.
  python3 wasm_diff.py VUC.wasm NATIVE_VUC STD_DIR FILE.vu..."""
import os, shutil, subprocess, sys, tempfile
import wasmtime

wasm, native, std = sys.argv[1], sys.argv[2], os.path.abspath(sys.argv[3])
# The compiler recurses as deep as the program nests. Native, its stack is 256 MB; wasm stacks are
# small (wasmtime's at most 2 MB, a browser's about 1 MB), so a program nested deeper than the stack
# allows traps instead, which counts as the native "nested too deeply" error.
cfg0 = wasmtime.Config()
cfg0.max_wasm_stack = (2 << 20) - (64 << 10)
eng = wasmtime.Engine(cfg0)
mod = wasmtime.Module.from_file(eng, wasm)
linker = wasmtime.Linker(eng)
linker.define_wasi()
tmp = tempfile.mkdtemp(prefix='vu-wasm-')

def run_wasm(cmd, name):
    store = wasmtime.Store(eng)
    cfg = wasmtime.WasiConfig()
    cfg.argv = ['vuc', cmd, '/w/' + name]
    cfg.env = [('VU_STD', '/std')]
    cfg.preopen_dir(std, '/std')
    cfg.preopen_dir(tmp, '/w')
    cfg.stderr_file = os.path.join(tmp, '.err')
    cfg.stdout_file = os.path.join(tmp, '.out')
    store.set_wasi(cfg)
    inst = linker.instantiate(store, mod)
    try:
        inst.exports(store)['_start'](store)
        code = 0
    except wasmtime.ExitTrap as e:
        code = e.code
    except wasmtime.Trap as e:
        if 'call stack exhausted' not in str(e): raise
        return 1, 'TOO DEEP'
    err = open(os.path.join(tmp, '.err'), encoding='utf-8', errors='replace').read()
    return code, err.replace('/w/' + name, os.path.join(tmp, name))

same = diff = 0
def main():
  global same, diff
  for f in sys.argv[4:]:
      name = os.path.basename(f)
      p = os.path.join(tmp, name)
      src = open(f, 'rb').read()
      for cmd in ('check', 'fmt'):
          open(p, 'wb').write(src)
          r = subprocess.run([native, cmd, p], capture_output=True, env={**os.environ, 'VU_STD': std})
          nat = (r.returncode, r.stderr.decode('utf-8', 'replace'), open(p, 'rb').read())
          open(p, 'wb').write(src)
          code, err = run_wasm(cmd, name)
          got = (code, err, open(p, 'rb').read())
          if got == nat or (got[1] == 'TOO DEEP' and nat[0] == 1 and 'nested too deeply' in nat[1]):
              same += 1
          else:
              diff += 1
              print(f'FAIL {cmd} {f}: native exit {nat[0]} {nat[1][:200]!r}, wasm exit {got[0]} {got[1][:200]!r}')
main()
shutil.rmtree(tmp)
print(f'{same} passed, {diff} failed')
sys.exit(1 if diff else 0)
