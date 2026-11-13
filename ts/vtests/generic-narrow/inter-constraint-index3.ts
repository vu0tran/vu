interface N { id: string; p: number }
interface IW { id: string; name: string; nodes: N[] }
type Base = Omit<IW, 'id' | 'name'> & { name: string | null };
declare const n: N;
function f<W extends Base>(w: W) { const a: W['nodes'][number] = n; const q: 'z' = a; return a; }
export { f };
