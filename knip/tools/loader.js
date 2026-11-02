// The source of loader.vu's LOADER_JS (tools/gen_loader.py writes it into loader.vu).
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';
import fs from 'node:fs';
import path from 'node:path';
const [outFile, reqFile, rootArg] = process.argv.slice(1);
const reqs = JSON.parse(fs.readFileSync(reqFile, 'utf8'));
const cwd = process.cwd();
// absolute paths inside the project come back project-relative, as "/x" (vknip's convention)
const absRoot = path.resolve(cwd, rootArg || '.');
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
  if (typeof v === 'string') return v === absRoot ? '/' : v.startsWith(absRoot + '/') ? v.slice(absRoot.length) : v;
  if (v === null || typeof v === 'boolean') return v;
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
// webpack's config as plugins/webpack findWebpackDependenciesFromConfig sees it: functions called
// (the config with env and argv, rule.use with the rule info, entry), ProvidePlugin definitions kept
const ruleInfo = { compiler: '', issuer: '', realResource: '', resource: '', resourceQuery: '', dependency: '', descriptionData: {}, issuerLayer: '' };
const evalRule = rule => {
  if (!rule || typeof rule !== 'object') return rule;
  const out = { ...rule };
  if (typeof out.use === 'function') out.use = out.use(ruleInfo);
  else if (out.use == null && typeof out.loader === 'function') out.loader = out.loader(ruleInfo);
  if (Array.isArray(out.oneOf)) out.oneOf = out.oneOf.map(evalRule);
  return out;
};
const evalWebpackOpts = async opts => {
  if (!opts || typeof opts !== 'object') return opts;
  const o = { ...opts };
  if (o.module && Array.isArray(o.module.rules)) o.module = { ...o.module, rules: o.module.rules.map(evalRule) };
  if (Array.isArray(o.plugins)) o.plugins = o.plugins.map(pl => (pl && pl.constructor && pl.constructor.name === 'ProvidePlugin' ? { __provide: pl.definitions ?? null } : null));
  let entry = typeof o.entry === 'function' ? await o.entry() : o.entry;
  if (entry && typeof entry === 'object' && !Array.isArray(entry)) {
    const e = {};
    for (const [k, item] of Object.entries(entry)) e[k] = typeof item === 'function' ? item() : item;
    entry = e;
  }
  o.entry = entry;
  return o;
};
const webpackPasses = async (config, isProduction) => {
  const passes = typeof config === 'function' ? [false, true] : [isProduction];
  const out = [];
  for (const prod of passes) {
    const mode = prod ? 'production' : 'development';
    const resolved = typeof config === 'function' ? await config({ production: prod, mode }, { mode }) : config;
    const configs = [];
    for (const opts of [resolved].flat()) configs.push(await evalWebpackOpts(opts));
    out.push({ production: prod, configs });
  }
  return out;
};
// the globals plugins define before loading their configs (setup)
const setups = { nuxt: 'defineNuxtConfig', nitro: 'defineNitroConfig' };
for (const r of reqs) {
  try {
    const g = setups[r.mode];
    if (g && !(g in globalThis)) Object.defineProperty(globalThis, g, { value: id => id, writable: true, configurable: true });
    let v = await settle(await load(r.file), 0);
    if (r.mode === 'vite') v = await viteConfigs(v);
    if (r.mode === 'next' && typeof v === 'function') v = await v('phase-production-build', { defaultConfig: {} });
    if (r.mode === 'webpack') v = await webpackPasses(v, r.args[0] === true);
    if (r.mode === 'expo' && typeof v === 'function') {
      const root = path.dirname(path.resolve(cwd, r.file));
      v = await v({ projectRoot: root, staticConfigPath: null, packageJsonPath: path.join(root, 'package.json'), config: { plugins: [] } });
    }
    if (r.mode === 'react-router') {
      const cfg = v ?? {};
      const appDir = path.resolve(path.dirname(path.resolve(cwd, r.file)), cfg.appDirectory ?? 'app');
      globalThis.__reactRouterAppDirectory = appDir;
      let routes = [];
      for (const f of ['routes.ts', 'routes.js']) {
        const rf = path.join(appDir, f);
        if (fs.existsSync(rf)) { routes = await settle(await load(rf), 0); break; }
      }
      v = { config: cfg, appDir, routes };
    }
    if (r.mode === 'rsbuild') {
      const params = [{ env: 'development', command: 'dev', envMode: 'development' }, { env: 'production', command: 'build', envMode: 'production' }];
      const configs = typeof v === 'function' ? await Promise.all(params.map(pp => v(pp))) : [v];
      const isProd = r.args[0] === true;
      const evalTools = async (local, top) => {
        const out = { ...local };
        const rspack = local?.tools?.rspack;
        if (!rspack) return out;
        const target = local.output?.target ?? top.output?.target ?? 'web';
        const mode = local.mode ?? top.mode;
        const passes = mode ? [mode === 'production'] : isProd ? [true] : [false, true];
        const results = [];
        for (const rs of [rspack].flat()) {
          for (const prod of typeof rs === 'function' ? passes : [isProd]) {
            const base = { mode: mode ?? (prod ? 'production' : 'development'), entry: {}, resolve: { alias: {} }, module: { rules: [] }, plugins: [] };
            const utils = { env: process.env.NODE_ENV ?? '', isDev: base.mode === 'development', isProd: base.mode === 'production', target, isServer: target === 'node', isWebWorker: target === 'web-worker' };
            const resolved = typeof rs === 'function' ? await rs(base, utils) : rs;
            results.push(...(await webpackPasses(resolved ?? base, isProd || prod)));
          }
        }
        out.tools = { ...local.tools, rspack: results };
        return out;
      };
      const all = [];
      for (const c of configs) {
        const envs = [];
        for (const e of Object.values(c?.environments ?? {})) envs.push(await evalTools(e, c));
        all.push({ ...(await evalTools(c, c)), environments: envs });
      }
      v = all;
    }
    if (r.mode === 'docusaurus' && v && typeof v === 'object') {
      const evalItems = async items => {
        const out = [];
        for (let item of items ?? []) {
          if (typeof item === 'function') item = item();
          if (item && !Array.isArray(item) && typeof item === 'object' && typeof item.configureWebpack === 'function') {
            const cfg = item.configureWebpack({}, false, { getStyleLoaders: () => [], getJSLoader: () => null });
            out.push({ __webpack: await webpackPasses(cfg, r.args[0] === true) });
          } else out.push(item);
        }
        return out;
      };
      v = { ...v, themes: await evalItems(v.themes), plugins: await evalItems(v.plugins), presets: await evalItems(v.presets) };
    }
    if (r.mode === 'electron-forge' && v && typeof v === 'object') {
      const mark = item => (item && typeof item === 'object' && !Array.isArray(item) ? { ...item, __plain: Object.getPrototypeOf(item) === Object.prototype, __name: item.name } : item);
      const arr = x => (Array.isArray(x) ? x : x === undefined ? [] : [x]);
      const forge = { ...v, makers: arr(v.makers).map(mark), publishers: arr(v.publishers).map(mark), plugins: arr(v.plugins).map(mark) };
      for (const item of forge.plugins) {
        const c = item && item.config;
        if (c && typeof c === 'object') {
          const wp = async x => (x && typeof x === 'object' ? { __webpack: await webpackPasses(x, r.args[0] === true) } : x);
          c.mainConfig = await wp(c.mainConfig);
          for (const rd of arr(c.renderer)) if (rd && typeof rd === 'object') {
            rd.config = await wp(rd.config);
            for (const ep of arr(rd.entryPoints)) if (ep && ep.preload && typeof ep.preload === 'object') ep.preload.config = await wp(ep.preload.config);
          }
        }
      }
      v = forge;
    }
    if (r.mode === 'karma') {
      if (typeof v !== 'function') v = null;
      else { const mem = { config: undefined, set(c) { this.config = c; } }; await v(mem); v = mem.config ?? {}; }
    }
    if (r.mode === 'vue' && v && v.configureWebpack) {
      const base = { mode: 'development', entry: {}, resolve: {}, plugins: [], module: { rules: [] } };
      const cw = typeof v.configureWebpack === 'function' ? v.configureWebpack(base) : v.configureWebpack;
      v = { ...v, configureWebpack: await webpackPasses(cw ?? base, r.args[0] === true) };
    }
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
