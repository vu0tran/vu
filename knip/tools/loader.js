// The source of loader.vu's LOADER_JS (tools/gen_loader.py writes it into loader.vu).
import { createRequire } from 'node:module';
import { pathToFileURL, fileURLToPath } from 'node:url';
import fs from 'node:fs';
import path from 'node:path';
import { StringDecoder } from 'node:string_decoder';
// One process serves the whole run: each line vknip writes to fd 3 is a request {root, reqs}, and
// the answer (the value of each file) is a line on fd 4. The process ends when fd 3 closes.
const cwd = process.cwd();
// absolute paths inside the project come back project-relative, as "/x" (vknip's convention)
let absRoot = cwd;
let jiti = null;
let jitiInst = null;
// jiti as knip has it: the project's, else the one next to its knip, else any in node_modules/.pnpm
// (looked for from the project's folder, then from the working one: they differ with --directory)
const findJiti = () => {
  for (const base of new Set([absRoot, cwd])) {
    const req = createRequire(path.join(base, 'package.json'));
    try { return req.resolve('jiti'); } catch {}
    try { return createRequire(req.resolve('knip')).resolve('jiti'); } catch {}
    try { return createRequire(fs.realpathSync(path.join(base, 'node_modules/knip/package.json'))).resolve('jiti'); } catch {}
    try {
      const pnpm = path.join(base, 'node_modules/.pnpm');
      const dirs = fs.readdirSync(pnpm).filter(d => /^jiti@2/.test(d)).sort().reverse();
      for (const d of dirs) { const f = path.join(pnpm, d, 'node_modules/jiti'); if (fs.existsSync(f)) return createRequire(path.join(f, 'package.json')).resolve('jiti'); }
    } catch {}
  }
  return null;
};
// (made at the first request, which names the project's folder; as knip's, for the working folder)
let jitiReady = false;
const initJiti = () => {
  if (jitiReady) return;
  jitiReady = true;
  try {
    const jp = findJiti();
    const j = createRequire(path.join(cwd, 'package.json'))(jp);
    const opts = { jsx: true, tsconfigPaths: true, interopDefault: true, alias: { '@rushstack/eslint-patch/modern-module-resolution': 'node:path', '@rushstack/eslint-config/patch/modern-module-resolution': 'node:path' } };
    const create = j.createJiti || (j.default && j.default.createJiti) || (typeof j === 'function' ? j : null);
    const inst = create(cwd, opts);
    if (typeof inst.import === 'function') { jiti = f => inst.import(f, { default: true }); jitiInst = inst; }
    else jiti = async f => { const m = inst(f); return m && m.default !== undefined ? m.default : m; };
  } catch {}
};
// Configs often import a package only for its define helper (defineConfig from vite, defineBuildConfig
// from unbuild), an identity function or nearly, and loading the package for it can take most of a
// run (vite or unbuild: half a second each). In a TypeScript config, the leading imports of nothing
// but such helpers become the helpers themselves, when the specifier resolves as jiti resolves it (so
// a package that's missing fails as before), to the package itself (its package.json names its
// repository) at a version that has them, and its entry file names each helper. A helper called in a
// way it doesn't cover (BAIL), or anything else, loads the file as it is.
const BAIL = new Error('vknip: load the file as it is');
const one = f => (...a) => { if (a.length !== 1) throw BAIL; return f(a[0]); };
const identity = () => one(c => c);
const PURE = {
  vite: { repo: 'vitejs/vite', min: 2, helpers: { defineConfig: identity } },
  'vitest/config': { repo: 'vitest-dev/vitest', min: 0, helpers: { defineConfig: identity, defineProject: identity, defineWorkspace: identity } },
  // (unbuild 2 made it return a list)
  unbuild: { repo: 'unjs/unbuild', min: 1, helpers: { defineBuildConfig: major => (major >= 2 ? one(c => (Array.isArray(c) ? c : [c]).filter(Boolean)) : identity()) } },
  tsdown: { repo: 'rolldown/tsdown', min: 0, helpers: { defineConfig: identity } },
  'tsdown/config': { repo: 'rolldown/tsdown', min: 0, helpers: { defineConfig: identity } },
  'astro/config': { repo: 'withastro/astro', min: 2, helpers: { defineConfig: identity } },
  vitepress: { repo: 'vuejs/vitepress', min: 1, helpers: { defineConfig: identity, defineConfigWithTheme: identity } },
  // (its entry re-exports playwright/test; with one config, defineConfig returns it, marked with a symbol)
  '@playwright/test': { repo: 'microsoft/playwright', min: 1, minor: 40, reexports: true, helpers: { defineConfig: identity } },
};
// the file's leading import declarations of only such helpers: [start, end, specifier, [[name, local]]]
const pureImports = src => {
  const out = [];
  let i = 0;
  const n = src.length;
  const skip = () => {
    for (;;) {
      while (i < n && /\s/.test(src[i])) i++;
      if (src.startsWith('//', i)) { const e = src.indexOf('\n', i); i = e < 0 ? n : e + 1; }
      else if (src.startsWith('/*', i)) { const e = src.indexOf('*/', i + 2); if (e < 0) return false; i = e + 2; }
      else return i < n;
    }
  };
  const named = /import\s*\{([^}'"`]*)\}\s*from\s*(['"])([^'"\n]+)\2[ \t]*;?/y;
  const other = /import(\s+[\w$]+\s*(,\s*\{[^}'"`]*\}|,\s*\*\s*as\s+[\w$]+)?|\s+type\s+[^'"`;]*?|\s*\*\s*as\s+[\w$]+)\s+from\s*(['"])[^'"\n]+\3[ \t]*;?|import\s*(['"])[^'"\n]+\4[ \t]*;?/y;
  while (skip()) {
    named.lastIndex = i;
    const m = named.exec(src);
    if (m) {
      const start = i;
      i = named.lastIndex;
      const helpers = PURE[m[3]]?.helpers;
      if (!helpers) continue;
      const names = [];
      let ok = true;
      for (let item of m[1].replace(/\/\*[\s\S]*?\*\//g, ' ').replace(/\/\/[^\n]*/g, ' ').split(',')) {
        item = item.trim();
        if (item === '' || /^type\s/.test(item)) continue;
        const mm = /^([\w$]+)(?:\s+as\s+([\w$]+))?$/.exec(item);
        if (!mm || !Object.hasOwn(helpers, mm[1])) { ok = false; break; }
        names.push([mm[1], mm[2] || mm[1]]);
      }
      if (ok && names.length > 0) out.push([start, i, m[3], names]);
      continue;
    }
    other.lastIndex = i;
    if (other.exec(src)) { i = other.lastIndex; continue; }
    break;
  }
  return out;
};
// the package.json of the package a resolved file belongs to
const pkgOf = (file, spec) => {
  const name = spec.startsWith('@') ? spec.split('/').slice(0, 2).join('/') : spec.split('/')[0];
  for (let d = path.dirname(file); ; d = path.dirname(d)) {
    try {
      const j = JSON.parse(fs.readFileSync(path.join(d, 'package.json'), 'utf8'));
      if (j.name === name) return j;
    } catch {}
    if (path.dirname(d) === d) return null;
  }
};
let shimN = 0;
const NOT = Symbol('not');
const loadPure = async abs => {
  // (VKNIP_NO_PURE=1 loads every file as it is: for comparing)
  if (!jitiInst || process.env.VKNIP_NO_PURE || typeof jitiInst.evalModule !== 'function' || typeof jitiInst.esmResolve !== 'function') return NOT;
  const ext = path.extname(abs);
  if (!/^\.[cm]?tsx?$/.test(ext) || jitiInst.cache?.[abs]) return NOT;
  let src;
  try { src = fs.readFileSync(abs, 'utf8'); } catch { return NOT; }
  const found = pureImports(src);
  if (found.length === 0) return NOT;
  const key = `__vknip_pure${shimN++}`;
  const vals = [];
  let text = src;
  for (let k = found.length - 1; k >= 0; k--) {
    const [start, end, spec, names] = found[k];
    let file;
    try {
      const r = jitiInst.esmResolve(spec, { parentURL: pathToFileURL(abs).href, try: true });
      file = r && (r.startsWith('file:') ? fileURLToPath(r) : r);
    } catch {}
    if (!file || !fs.existsSync(file)) continue;
    const pure = PURE[spec];
    const pj = pkgOf(file, spec);
    const repo = pj && (typeof pj.repository === 'string' ? pj.repository : pj.repository?.url);
    const major = pj ? parseInt(String(pj.version), 10) : NaN;
    if (typeof repo !== 'string' || !repo.includes(pure.repo) || !(major >= pure.min)) continue;
    if (pure.minor !== undefined && major === pure.min && !(parseInt(String(pj.version).split('.')[1], 10) >= pure.minor)) continue;
    let entry = '';
    try { entry = fs.readFileSync(file, 'utf8'); } catch {}
    if (!pure.reexports && !names.every(([name]) => new RegExp(`\\b${name}\\b`).test(entry))) continue;
    const helpers = {};
    for (const [name] of names) helpers[name] = pure.helpers[name](major);
    vals.push(helpers);
    const decl = `const { ${names.map(([a, b]) => `${a}: ${b}`).join(', ')} } = globalThis.${key}[${vals.length - 1}];`;
    // (the declaration in the import's place, its lines kept)
    const lines = src.slice(start, end).split('\n').length - 1;
    text = text.slice(0, start) + decl + '\n'.repeat(lines) + text.slice(end);
  }
  if (vals.length === 0) return NOT;
  globalThis[key] = vals;
  try {
    const m = await jitiInst.evalModule(text, { id: abs, filename: abs, ext, async: true });
    return m?.default ?? m;
  } catch (e) {
    if (e !== BAIL) throw e;
    if (jitiInst.cache) delete jitiInst.cache[abs];
    return NOT;
  } finally { delete globalThis[key]; }
};
const load = async file => {
  const abs = path.resolve(cwd, file);
  if (jiti) {
    const v = await loadPure(abs);
    return v === NOT ? await jiti(abs) : v;
  }
  const m = await import(pathToFileURL(abs).href);
  return m.default ?? m;
};
const relKey = k => (k === absRoot ? '/' : k.startsWith(absRoot + '/') ? k.slice(absRoot.length) : k);
const enc = (v, depth, seen) => {
  if (v === undefined || typeof v === 'symbol') return undefined;
  if (typeof v === 'string') return v === absRoot ? '/' : v.startsWith(absRoot + '/') ? v.slice(absRoot.length) : v;
  if (v === null || typeof v === 'boolean') return v;
  if (typeof v === 'number') return Number.isFinite(v) ? v : null;
  if (typeof v === 'bigint') return String(v);
  if (typeof v === 'function') return { '__vknip_fn': v.name || '' };
  if (v instanceof RegExp) return { '__vknip_re': v.source, flags: v.flags };
  if (v instanceof Promise) return { '__vknip_promise': 1 };
  if (depth > 40 || seen.has(v)) return { '__vknip_cycle': 1 };
  seen.add(v);
  let out;
  if (Array.isArray(v) || v instanceof Set) out = Array.from(v, x => { const e = enc(x, depth + 1, seen); return e === undefined ? null : e; });
  else if (v instanceof Map) { out = {}; for (const [k, x] of v) { const e = enc(x, depth + 1, seen); if (e !== undefined) out[String(k)] = e; } }
  else if (v instanceof URL) out = v.href;
  else { out = {}; let n = 0; for (const k of Object.keys(v)) { if (++n > 400) break; let x; try { x = v[k]; } catch { continue; } const e = enc(x, depth + 1, seen); if (e !== undefined) out[relKey(k)] = e; } }
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
  if (!config?.test?.projects) return out;
  // (the expression knip iterates, so a value that isn't iterable fails with the same message)
  for (const project of config.test.projects) {
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
// webpack's config as plugins/webpack findWebpackDependenciesFromConfig sees it: functions called
// (the config with env and argv, rule.use with the rule info, entry), ProvidePlugin definitions kept
const ruleInfo = { compiler: '', issuer: '', realResource: '', resource: '', resourceQuery: '', dependency: '', descriptionData: {}, issuerLayer: '' };
const evalRule = rule => {
  if (typeof rule === 'function') { const r = rule(ruleInfo); return typeof r === 'string' ? { loader: r } : r; }
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
// plugins/eleventy/helpers DummyEleventyConfig (what a config function receives)
class DummyEleventyConfig {
  constructor() {
    this._uniqueId = {};
    this.events = {};
    this.benchmarkManager = {};
    this.benchmarks = {};
    this.collections = {};
    this.precompiledCollections = {};
    this.templateFormats = {};
    this.liquidOptions = {};
    this.liquidTags = {};
    this.liquidFilters = {};
    this.liquidShortcodes = {};
    this.liquidPairedShortcodes = {};
    this.nunjucksEnvironmentOptions = {};
    this.nunjucksPrecompiledTemplates = {};
    this.nunjucksFilters = {};
    this.nunjucksAsyncFilters = {};
    this.nunjucksTags = {};
    this.nunjucksGlobals = {};
    this.nunjucksShortcodes = {};
    this.nunjucksAsyncShortcodes = {};
    this.nunjucksPairedShortcodes = {};
    this.nunjucksAsyncPairedShortcodes = {};
    this.javascriptFunctions = {};
    this.markdownHighlighter = null;
    this.libraryOverrides = {};
    this.passthroughCopies = {};
    this.layoutAliases = {};
    this.layoutResolution = true;
    this.linters = {};
    this.transforms = {};
    this.activeNamespace = '';
    this.DateTime = {};
    this.dynamicPermalinks = true;
    this.useGitIgnore = true;
    this.ignores = new Set();
    this.watchIgnores = new Set();
    this.dataDeepMerge = true;
    this.extensionMap = new Set();
    this.watchJavaScriptDependencies = true;
    this.additionalWatchTargets = [];
    this.serverOptions = {};
    this.globalData = {};
    this.chokidarConfig = {};
    this.watchThrottleWaitTime = 0;
    this.dataExtensions = new Map();
    this.quietMode = false;
    this.plugins = [];
    this._pluginExecution = false;
    this.useTemplateCache = true;
    this.dataFilterSelectors = new Set();
    this.libraryAmendments = {};
    this.serverPassthroughCopyBehavior = '';
    this.urlTransforms = [];
    this.dataFileSuffixesOverride = false;
    this.dataFileDirBaseNameOverride = false;
    this.templateFormatsAdded = {};
    this.frontMatterParsingOptions = { engines: {} };
  }
  _getUniqueId() {}
  reset() {}
  versionCheck() {}
  on() {}
  emit() {}
  _enablePluginExecution() {}
  addMarkdownHighlighter() {}
  addLiquidTag() {}
  addLiquidFilter() {}
  addNunjucksAsyncFilter() {}
  addNunjucksFilter() {}
  addHandlebarsHelper() {}
  addFilter() {}
  addAsyncFilter() {}
  getFilter() {}
  addNunjucksTag() {}
  addGlobalData() {}
  addNunjucksGlobal() {}
  addTransform() {}
  addLinter() {}
  addLayoutAlias() {}
  setLayoutResolution() {}
  enableLayoutResolution() {}
  getCollections() {}
  addCollection() {}
  addPlugin() {}
  _getPluginName() {}
  _executePlugin() {}
  getNamespacedName() {}
  namespace() {}
  _normalizeTemplateFormats() {}
  setTemplateFormats() {}
  addTemplateFormats() {}
  setLibrary() {}
  amendLibrary() {}
  setPugOptions() {}
  setLiquidOptions() {}
  setNunjucksEnvironmentOptions() {}
  setNunjucksPrecompiledTemplates() {}
  setEjsOptions() {}
  setDynamicPermalinks() {}
  setUseGitIgnore() {}
  addShortcode() {}
  addAsyncShortcode() {}
  addNunjucksAsyncShortcode() {}
  addNunjucksShortcode() {}
  addLiquidShortcode() {}
  addHandlebarsShortcode() {}
  addPairedShortcode() {}
  addPairedAsyncShortcode() {}
  addPairedNunjucksAsyncShortcode() {}
  addPairedNunjucksShortcode() {}
  addPairedLiquidShortcode() {}
  addPairedHandlebarsShortcode() {}
  addJavaScriptFunction() {}
  setDataDeepMerge() {}
  isDataDeepMergeModified() {}
  addWatchTarget() {}
  setWatchJavaScriptDependencies() {}
  setServerOptions() {}
  setBrowserSyncConfig() {}
  setChokidarConfig() {}
  setWatchThrottleWaitTime() {}
  setFrontMatterParsingOptions() {}
  setQuietMode() {}
  addExtension() {}
  addDataExtension() {}
  setUseTemplateCache() {}
  setPrecompiledCollections() {}
  setServerPassthroughCopyBehavior() {}
  addUrlTransform() {}
  setDataFileSuffixes() {}
  setDataFileBaseName() {}
  getMergingConfigObject() {}
  isVirtualTemplate() {}
  setInputDirectory() {}
  setOutputDirectory() {}
  setDataDirectory() {}
  setIncludesDirectory() {}
  setLayoutsDirectory() {}
  setFreezeReservedData() {}
  addDateParsing() {}
  addBundle() {}
  addPassthroughCopy(input) { if (typeof input === 'string') this.passthroughCopies[input] = {}; else for (const [p] of Object.entries(input)) this.passthroughCopies[p] = {}; }
}
// the globals plugins define before loading their configs (setup)
const setups = { nuxt: 'defineNuxtConfig', nitro: 'defineNitroConfig' };
// plugins/_vue/auto-import getVueSfc and collectTemplateInfo (template expressions kept as text)
const vueSfcInfo = (root, files) => {
  let sfc = null;
  try { sfc = createRequire(path.join(path.resolve(cwd, root), 'package.json'))('vue/compiler-sfc'); } catch {}
  const res = [];
  for (const f of files) {
    if (!sfc) { res.push(null); continue; }
    try {
      const abs = path.resolve(cwd, f);
      const source = fs.readFileSync(abs, 'utf8');
      let descriptor, compileTemplate = null;
      if (typeof sfc.parseComponent === 'function') {
        descriptor = sfc.parse({ source, filename: abs, sourceMap: false });
        compileTemplate = (src, isTS, preprocessLang) => sfc.compileTemplate({ source: src, filename: abs, sourceMap: false, isProduction: true, prettify: false, isTS, preprocessLang });
      } else descriptor = sfc.parse(source, { filename: abs, sourceMap: false }).descriptor;
      const scripts = [];
      if (descriptor.script?.content) scripts.push(descriptor.script.content);
      if (descriptor.scriptSetup?.content) scripts.push(descriptor.scriptSetup.content);
      const template = descriptor.template;
      const isTS = ['ts', 'tsx'].includes(descriptor.script?.lang) || ['ts', 'tsx'].includes(descriptor.scriptSetup?.lang);
      const compiled = template && !template.ast && compileTemplate ? compileTemplate(template.content, isTS, template.lang) : undefined;
      const ast = template?.ast ?? compiled?.ast;
      let tags = null;
      const exprs = [];
      if (ast) {
        const t = new Set();
        const visited = new Set();
        const visit = node => {
          if (!node || visited.has(node)) return;
          visited.add(node);
          if (node.tag) t.add(node.tag);
          if (node.type === 5 && node.content && !node.content.isStatic) exprs.push(node.content.content);
          if (node.props) for (const prop of node.props) if (prop.type === 7) {
            if (prop.exp && !prop.exp.isStatic) exprs.push(prop.exp.content);
            if (prop.arg && !prop.arg.isStatic) exprs.push(prop.arg.content);
          }
          if (node.children) for (const c of node.children) visit(c);
          if (node.ifConditions) for (const c of node.ifConditions) visit(c.block);
          if (node.scopedSlots) for (const n in node.scopedSlots) visit(node.scopedSlots[n]);
        };
        visit(ast);
        tags = [...t];
      }
      res.push({ scripts, tags, exprs: exprs.map(String), code: compiled?.code ? String(compiled.code) : null });
    } catch (e) {
      res.push({ error: (e && e.message ? e.message : String(e)).split('\n')[0] });
    }
  }
  return res;
};
// the configuration's compilers (normalizeCompilers), each file compiled with its extension's
const customCompile = async (config, files) => {
  if (typeof config === 'function') config = await config();
  const compilers = new Map();
  for (const ext in config?.compilers ?? {}) { const fn = config.compilers[ext]; if (typeof fn === 'function') compilers.set(ext.replace(/^\.*/, '.'), fn); }
  for (const ext in config?.asyncCompilers ?? {}) compilers.set(ext.replace(/^\.*/, '.'), config.asyncCompilers[ext]);
  const res = [];
  for (const [ext, f] of files) {
    const abs = path.resolve(cwd, f);
    try {
      const text = fs.readFileSync(abs, 'utf8');
      let result = compilers.get(ext)(text, abs);
      if (result !== null && (typeof result === 'object' || typeof result === 'function')) result = await result;
      if (typeof result !== 'string') { res.push({ config: `Compiler for ${ext} returned ${result === null ? 'null' : typeof result} for ${abs}; expected a string or PromiseLike<string>` }); continue; }
      res.push({ ok: result });
    } catch (e) {
      res.push({ error: `Compiler for ${ext} failed (${abs})`, reason: e && e.message !== undefined ? String(e.message) : String(e) });
    }
  }
  return res;
};
// preprocessors and custom reporters (util/preprocessor.ts, util/reporter.ts): modules loaded as
// knip's _load does; a module that fails to load is a LoaderError
const loadModule = async spec => {
  const isLocal = spec.startsWith('.') || spec.startsWith('/');
  const file = isLocal ? path.resolve(cwd, spec) : spec;
  try {
    if (isLocal) return await load(file);
    // (a package: as knip's jiti.import, relative to the folder)
    if (jiti) return await jiti(file);
    const m = await import(file);
    return m.default ?? m;
  }
  catch (e) { const err = new Error(`Error loading ${file}`); err.reason = e && e.message !== undefined ? String(e.message) : String(e); err.notFound = !!(e && e.code === 'MODULE_NOT_FOUND'); throw err; }
};
const toPlain = data => JSON.parse(JSON.stringify(data, (k, v) => (v instanceof Set ? [...v] : v instanceof Map ? Object.fromEntries(v) : v instanceof RegExp ? { __vknip_re: v.source, flags: v.flags } : v)));
const fromPlain = data => ({ ...data, tagHints: new Set(data.tagHints ?? []), configurationHints: (data.configurationHints ?? []).map(h => (h && h.identifier && h.identifier.__vknip_re !== undefined ? { ...h, identifier: new RegExp(h.identifier.__vknip_re, h.identifier.flags) } : h)) });
// (what a module prints is captured, and printed by vknip in its place)
const captured = async f => {
  let out = '', err = '';
  const ow = process.stdout.write.bind(process.stdout), ew = process.stderr.write.bind(process.stderr);
  process.stdout.write = c => { out += String(c); return true; };
  process.stderr.write = c => { err += String(c); return true; };
  try { const value = await f(t => { out += t; }); return { value, out, err }; }
  catch (e) { e.out = out; e.errOut = err; throw e; }
  finally { process.stdout.write = ow; process.stderr.write = ew; }
};
const runPreprocessors = async (mods, data) => {
  const fns = [];
  for (const m of mods) fns.push(await loadModule(m));
  const r = await captured(async () => {
    let d = fromPlain(data);
    for (const fn of fns) d = await fn(d);
    return toPlain(d);
  });
  return { data: r.value, out: r.out, err: r.err };
};
const runReporter = async (mod, data, toFile) => {
  const fn = await loadModule(mod);
  let file = '';
  const r = await captured(async add => {
    const write = toFile ? text => { if (text) file += `${text}\n`; } : text => { if (text) add(`${text}\n`); };
    await fn({ ...fromPlain(data), write });
  });
  return { out: r.out, err: r.err, file };
};
// the yaml package (knip's YAML parser): the project's, the one next to its knip, else any in .pnpm
const findYaml = () => {
  const tries = [];
  for (const base of new Set([absRoot, cwd])) tries.push(
    () => createRequire(path.join(base, 'package.json'))('yaml'),
    () => createRequire(createRequire(path.join(base, 'package.json')).resolve('knip'))('yaml'),
    () => createRequire(fs.realpathSync(path.join(base, 'node_modules/knip/package.json')))('yaml'),
    () => {
      const pnpm = path.join(base, 'node_modules/.pnpm');
      const dirs = fs.readdirSync(pnpm).filter(d => /^yaml@2/.test(d)).sort().reverse();
      for (const d of dirs) { const f = path.join(pnpm, d, 'node_modules/yaml/package.json'); if (fs.existsSync(f)) return createRequire(f)('yaml'); }
      return null;
    },
  );
  for (const t of tries) { try { const y = t(); if (y && typeof y.parse === 'function') return y; } catch {} }
  return null;
};
const handle = async reqs => {
const out = {};
// (the globals a request's setup defines are gone after it, as when each mode had its own process)
const defined = [];
for (const r of reqs) {
  // a YAML file vknip's reader isn't sure about: parsed as knip parses it (loadYAML)
  if (r.mode === 'yaml') {
    const Y = findYaml();
    if (!Y) { out[r.file] = { noyaml: true }; continue; }
    try { out[r.file] = { ok: enc(Y.parse(fs.readFileSync(path.resolve(cwd, r.file), 'utf8'), { logLevel: 'error' }), 0, new Set()) ?? null }; }
    catch (e) { out[r.file] = { error: (e && e.message ? e.message : String(e)).split('\n')[0] }; }
    continue;
  }
  if (r.mode === 'preprocess' || r.mode === 'reporter') {
    try {
      out[r.file] = { ok: r.mode === 'preprocess' ? await runPreprocessors(r.args.mods, r.args.data) : await runReporter(r.args.mod, r.args.data, r.args.toFile) };
    } catch (e) { out[r.file] = { error: e && e.message ? e.message.split('\n')[0] : String(e), reason: e && e.reason !== undefined ? e.reason : '', loader: !!(e && e.reason !== undefined), notFound: !!(e && e.notFound), out: (e && e.out) || '', errOut: (e && e.errOut) || '', stack: e && e.stack ? String(e.stack) : String(e) }; }
    continue;
  }
  if (r.mode === 'vue-sfc') { out[r.file] = { ok: vueSfcInfo(r.file, r.args) }; continue; }
  if (r.mode === 'compile') {
    try { out[r.file] = { ok: await customCompile(await load(r.file), r.args) }; }
    catch (e) { out[r.file] = { error: (e && e.message ? e.message : String(e)).split('\n')[0] }; }
    continue;
  }
  // (what the config prints goes back with its value: vknip prints it where knip loads the file)
  let cout = '', cerr = '';
  const ow = process.stdout.write, ew = process.stderr.write;
  const grab = add => (c, ...rest) => { add(typeof c === 'string' ? c : Buffer.from(c).toString()); const cb = rest.find(x => typeof x === 'function'); if (cb) cb(); return true; };
  process.stdout.write = grab(t => { cout += t; });
  process.stderr.write = grab(t => { cerr += t; });
  try {
    const g = setups[r.mode];
    if (g && !(g in globalThis)) { Object.defineProperty(globalThis, g, { value: id => id, writable: true, configurable: true }); defined.push(g); }
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
    if (r.mode === 'electron-vite') {
      const env = { command: 'build', mode: 'production' };
      const cfg = typeof v === 'function' ? await v(env) : v;
      const out = { ...(cfg ?? {}) };
      for (const name of ['main', 'preload', 'renderer']) if (typeof out[name] === 'function') out[name] = await out[name](env);
      v = out;
    }
    if (r.mode === 'storybook' && v && typeof v.stories === 'function') v = { ...v, stories: await v.stories(['**/*.@(mdx|stories.@(mdx|js|jsx|mjs|ts|tsx))']) };
    if (r.mode === 'rstest' && typeof v === 'function') v = await v({ env: 'test', command: 'run', envMode: 'test' });
    if (r.mode === 'babel' && typeof v === 'function') {
      const cacheFn = () => void 0;
      cacheFn.forever = () => cacheFn; cacheFn.never = () => cacheFn; cacheFn.using = () => cacheFn; cacheFn.invalidate = () => cacheFn;
      v = v({ assertVersion: () => true, cache: cacheFn, caller: () => true, env: env => (typeof env === 'string' ? true : 'development'), version: '0.0.0' });
    }
    if (r.mode === 'lint-staged') {
      const cfg = typeof v === 'function' ? await v([]) : v;
      const resolveEntry = async value => {
        if (Array.isArray(value)) return (await Promise.all(value.map(resolveEntry))).flat();
        if (typeof value === 'function') return [await value([])].flat().filter(item => typeof item === 'string');
        return typeof value === 'string' ? [value] : [];
      };
      if (cfg && typeof cfg === 'object') { const o = {}; for (const [k, e] of Object.entries(cfg)) o[k] = await resolveEntry(e); v = o; } else v = cfg;
    }
    if (r.mode === 'eleventy') {
      const dummy = new DummyEleventyConfig();
      if (typeof v === 'function') v = await v(dummy);
      v = { config: v ?? null, passthrough: Object.keys(dummy.passthroughCopies) };
    }
    if (r.mode === 'call0' && typeof v === 'function') v = await v();
    if (r.mode === 'gatsby' && v && typeof v.onCreateBabelConfig === 'function') {
      const names = new Set();
      v.onCreateBabelConfig({ actions: { setBabelPlugin: plugin => names.add(plugin.name) } });
      v = { ...v, __babelPlugins: [...names] };
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
    // (knip's formatCauseMessage: paths in the project's folder relative to it)
    out[r.file] = { error: (root && root.message ? root.message : String(root)).split('\n')[0].replace(absRoot + '/', '') };
  } finally {
    process.stdout.write = ow;
    process.stderr.write = ew;
  }
  if (cout !== '') out[r.file].out = cout;
  if (cerr !== '') out[r.file].err = cerr;
}
for (const g of defined) delete globalThis[g];
return out;
};
// (requests are read synchronously: while one is handled nothing of the loader's keeps node alive, so
// a config whose promise never settles ends the process, as it ended the one-shot loader)
const inBuf = Buffer.alloc(65536);
const decoder = new StringDecoder('utf8');
let pending = '';
const readLine = () => {
  for (;;) {
    const nl = pending.indexOf('\n');
    if (nl >= 0) { const l = pending.slice(0, nl); pending = pending.slice(nl + 1); return l; }
    let n;
    try { n = fs.readSync(3, inBuf, 0, inBuf.length, null); }
    catch (e) { if (e.code === 'EAGAIN' || e.code === 'EINTR') continue; if (e.code === 'EOF') return null; throw e; }
    if (n === 0) return null;
    pending += decoder.write(inBuf.subarray(0, n));
  }
};
for (let line; (line = readLine()) !== null;) {
  let res;
  try {
    const q = JSON.parse(line);
    absRoot = path.resolve(cwd, q.root || '.');
    initJiti();
    if (q.warm) {
      // (getting ready while vknip reads the project: jiti's TypeScript transform)
      try { jitiInst?.transform?.({ source: 'export default {} as {}', filename: path.join(cwd, 'vknip-warm.ts'), ts: true }); } catch {}
      res = {};
    } else res = await handle(q.reqs);
  } catch (e) { res = { __vknip_error: e && e.message ? String(e.message).split('\n')[0] : String(e) }; }
  const buf = Buffer.from(JSON.stringify(res) + '\n');
  for (let off = 0; off < buf.length;) off += fs.writeSync(4, buf, off);
}
process.exit(0);
