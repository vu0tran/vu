interface IW { id: string; name: string; active: boolean; nodes: { p: number }[] }
type Base = Omit<IW, 'id' | 'name'> & { name: string | null };
function size<W extends Base>(w: W) { return w.nodes.reduce((a, x) => a + x.p, 0); }
export const s: 'z' = size;
function size2<W extends Base>(w: W) { return w.nodes; }
export const s2: 'z' = size2;
