export {};
interface NI<T extends string> { type: T; version: string }
interface GN { instance: NI<string> }
const ST = 'sticky';
const AG = 'agent';
declare function pv(v: string): number;
export function dims(nodes: ReadonlyMap<string, GN>, name: string) {
  const g = nodes.get(name);
  if (g?.instance.type === ST) return 1;
  if (g?.instance.type === AG && pv(g.instance.version) >= 2) return 2;
  return 3;
}
