declare const IN: readonly ["options", "buildStart"];
declare const OUT: readonly ["renderStart", "writeBundle"];
declare const ALL: [...typeof IN, ...typeof OUT, "footer"];
type DefinedHookNames = { readonly [K in (typeof ALL)[number]]: K };
interface FunctionPluginHooks {
  options(o: number): void;
  buildStart(): void;
  renderStart(): void;
  writeBundle(options: { dir?: string }): void;
}
type OutputPluginHooks = DefinedHookNames["renderStart" | "writeBundle"];
type PluginHooks = { [K in keyof FunctionPluginHooks]: FunctionPluginHooks[K] };
interface OutputPlugin extends Partial<{ [K in keyof PluginHooks as K & OutputPluginHooks]: PluginHooks[K] }> { name: string }
export const p: OutputPlugin = { name: "x", writeBundle(options) { void options.dir; } };
type Q = DefinedHookNames["writeBundle"];
export const q: Q = "writeBundle";
declare const NAMES: { readonly a: "alpha"; readonly n: 1 };
interface Hooks { [NAMES.a]: (x: number) => void; [NAMES.n]: string; ["lit"]: boolean }
export const h: Hooks = { alpha(x) { void x; }, 1: "s", lit: true };
export const bad: Hooks = { alpha: 1, 1: "s", lit: true };
export type K = keyof Hooks;
export const k: K = "nope";
