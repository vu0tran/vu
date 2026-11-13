interface IW { id: string; name: string; nodes: { p: number }[] }
type Base = Omit<IW, 'id' | 'name'> & { name: string | null };
declare function take(x: { p: number }[]): void;
function f<W extends Base>(w: W, k: W['nodes']) { take(k); const q: 'z' = k; }
export { f };
