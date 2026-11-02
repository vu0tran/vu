// Dumps the static fields of knip's plugins (dev-time extraction for vknip's plugin table).
import { Plugins, PluginEntries } from '/dev/shm/knip/ref/node_modules/knip/dist/plugins.js';
const enc = v => v instanceof RegExp ? { re: v.source, flags: v.flags } : v;
const out = [];
for (const [name, p] of PluginEntries) {
  const cfg = typeof p.config === 'function' ? { fn: String(p.config) } : p.config;
  out.push({
    name, title: p.title,
    enablers: Array.isArray(p.enablers) ? p.enablers.map(enc) : (typeof p.enablers === 'string' ? p.enablers : (p.enablers ? 'fn' : null)),
    isEnabled: p.isEnabled ? String(p.isEnabled) : null,
    isRootOnly: !!p.isRootOnly,
    packageJsonPath: typeof p.packageJsonPath === 'function' ? { fn: String(p.packageJsonPath) } : (p.packageJsonPath ?? null),
    config: cfg ?? null, entry: p.entry ?? null, production: p.production ?? null, project: p.project ?? null,
    resolveConfig: !!p.resolveConfig, resolveFromAST: !!p.resolveFromAST, resolve: !!p.resolve,
    isLoadConfig: !!p.isLoadConfig, resolveSourceMap: !!p.resolveSourceMap, registerCompilers: !!p.registerCompilers,
    registerVisitors: !!p.registerVisitors, isFilterTransitiveDependencies: !!p.isFilterTransitiveDependencies,
    isLoadConfigOptional: !!p.isLoadConfigOptional,
  });
}
console.log(JSON.stringify(out, null, 1));
