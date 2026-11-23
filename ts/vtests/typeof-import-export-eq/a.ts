interface Mods {
  "base": typeof import("base");
  "node:base": typeof import("node:base");
}
declare function get<K extends keyof Mods>(k: K): Mods[K];
const p = get("node:base");
const j: number = p.join("a", "b");
const q: number = get("base");
type N = typeof import("ns");
declare const n: N;
const s: string = n.v;
export {};
