// The source of loader.vu's LOADER_JS (tools/gen_loader.py writes it into loader.vu).
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import fs from 'node:fs';
import path from 'node:path';
const [outFile, reqFile] = process.argv.slice(1);
const reqs = JSON.parse(fs.readFileSync(reqFile, 'utf8'));
const cwd = process.cwd();
let jiti = null;
// jiti as knip has it: the project's, else the one next to its knip, else any in node_modules/.pnpm
const findJiti = () => {
  const req = createRequire(path.join(cwd, 'package.json'));
  try { return req.resolve('jiti'); } catch {}
  try { return createRequire(req.resolve('knip')).resolve('jiti'); } catch {}
  try { return createRequire(fs.realpathSync(path.join(cwd, 'node_modules/knip/package.json'))).resolve('jiti'); } catch {}
  try {
    const pnpm = path.join(cwd, 'node_modules/.pnpm');
    const dirs = fs.readdirSync(pnpm).filter(d => /^jiti@2/.test(d)).sort().reverse();
    for (const d of dirs) { const f = path.join(pnpm, d, 'node_modules/jiti'); if (fs.existsSync(f)) return createRequire(path.join(f, 'package.json')).resolve('jiti'); }
  } catch {}
  return null;
};
try {
  const jp = findJiti();
  const j = createRequire(path.join(cwd, 'package.json'))(jp);
  const opts = { jsx: true, tsconfigPaths: true, interopDefault: true, alias: { '@rushstack/eslint-patch/modern-module-resolution': 'node:path', '@rushstack/eslint-config/patch/modern-module-resolution': 'node:path' } };
  const create = j.createJiti || (j.default && j.default.createJiti) || (typeof j === 'function' ? j : null);
  const inst = create(path.join(cwd, 'x.js'), opts);
  if (typeof inst.import === 'function') jiti = f => inst.import(f, { default: true });
  else jiti = async f => { const m = inst(f); return m && m.default !== undefined ? m.default : m; };
} catch {}
const load = async file => {
  const abs = path.resolve(cwd, file);
  if (jiti) return await jiti(abs);
  const m = await import(pathToFileURL(abs).href);
  return m.default ?? m;
};
const enc = (v, depth, seen) => {
  if (v === undefined || typeof v === 'symbol') return undefined;
  if (v === null || typeof v === 'string' || typeof v === 'boolean') return v;
  if (typeof v === 'number') return Number.isFinite(v) ? v : null;
  if (typeof v === 'bigint') return String(v);
  if (typeof v === 'function') return { '__vknip_fn': v.name || '' };
  if (v instanceof RegExp) return { '__vknip_re': v.source, flags: v.flags };
  if (v instanceof Promise) return { '__vknip_promise': 1 };
  if (depth > 9 || seen.has(v)) return { '__vknip_cycle': 1 };
  seen.add(v);
  let out;
  if (Array.isArray(v) || v instanceof Set) out = Array.from(v, x => { const e = enc(x, depth + 1, seen); return e === undefined ? null : e; });
  else if (v instanceof Map) { out = {}; for (const [k, x] of v) { const e = enc(x, depth + 1, seen); if (e !== undefined) out[String(k)] = e; } }
  else if (v instanceof URL) out = v.href;
  else { out = {}; let n = 0; for (const k of Object.keys(v)) { if (++n > 400) break; let x; try { x = v[k]; } catch { continue; } const e = enc(x, depth + 1, seen); if (e !== undefined) out[k] = e; } }
  seen.delete(v);
  return out;
};
const settle = async (v, depth) => {
  v = await v;
  if (depth < 3 && Array.isArray(v)) return Promise.all(v.map(x => settle(x, depth + 1)));
  return v;
};
const viteEnvs = [];
for (const command of ['serve', 'build'])
  for (const mode of ['development', 'production'])
    for (const isSsrBuild of command === 'build' ? [undefined, false, true] : [undefined])
      viteEnvs.push({ command, mode, isSsrBuild, ssrBuild: isSsrBuild });
const projectEnv = { command: 'serve', mode: 'test', isPreview: false, isSsrBuild: false };
const projectConfigs = async (config, callFns) => {
  const out = [];
  for (const project of config?.test?.projects ?? []) {
    if (typeof project === 'function') { if (callFns) out.push(await project(projectEnv)); }
    else if (typeof project !== 'string') out.push(await project);
  }
  return out;
};
// vitest/index.js getConfigs: a function config is called for each command and mode
const viteConfigs = async local => {
  const configs = [];
  for (const config of [local].flat()) {
    if (config && typeof config !== 'string') {
      if (typeof config === 'function') {
        for (const env of viteEnvs) {
          const cfg = await config(env);
          configs.push(cfg, ...(await projectConfigs(cfg, env.command === 'serve' && env.mode === 'development')));
        }
      } else configs.push(config, ...(await projectConfigs(config, true)));
    }
  }
  return configs;
};
const out = {};
for (const r of reqs) {
  try {
    let v = await settle(await load(r.file), 0);
    if (r.mode === 'vite') v = await viteConfigs(v);
    if (r.mode === 'call') {
      const results = [];
      for (const a of r.args) results.push(typeof v === 'function' ? await settle(v(a), 0) : v);
      v = results;
    }
    out[r.file] = { ok: enc(v, 0, new Set()) ?? null };
  } catch (e) {
    let root = e;
    while (root && root.cause instanceof Error) root = root.cause;
    out[r.file] = { error: (root && root.message ? root.message : String(root)).split('\n')[0].replace(cwd + '/', '') };
  }
}
fs.writeFileSync(outFile, JSON.stringify(out));
process.exit(0);
