type Node0 = { id: string; name: string; extra: number };
type Base = Omit<{ nodes: Node0[]; id: string; active: boolean }, 'id' | 'active'> & { name: string | null };
type DN = Pick<Node0, 'id' | 'name'>;
type DW<N extends DN = DN> = { nodes: N[] };
class CS<T extends DN> {
  readonly nodes: Map<string, { node: T; s: number }>;
  constructor(from: DW<T>, to: DW<T>) { this.nodes = new Map(); }
}
type Rule<W extends Base = Base, N extends W['nodes'][number] = W['nodes'][number]> = (p: W, n: W, d: CS<N>) => boolean;
export function g<W extends Base = Base>(ws: W[], rules: Rule<W>[]) {
  const rem = [...ws];
  const wcs = new CS(rem[0], rem[1]);
  const z: 'z' = wcs;
  for (const r of rules) r(rem[0], rem[1], wcs);
}
