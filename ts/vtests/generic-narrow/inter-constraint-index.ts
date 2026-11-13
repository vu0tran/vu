interface IW { id: string; name: string; active: boolean; nodes: { p: number }[] }
type Base = Omit<IW, 'id' | 'name'> & { name: string | null };
function size<W extends Base>(w: W) { return w.nodes.reduce((a, x) => a + x.p, 0); }
export function group<W extends Base = Base>(ws: W[]) {
  const m = { s: ws.length ? size(ws[ws.length - 1]) : undefined };
  return m;
}
type N = Base['nodes'];
export const n: 'z' = null! as N;
function idx<W extends Base>(w: W): W['nodes'] { return w.nodes; }
export const i: 'z' = idx;
