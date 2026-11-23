// a function without a return value in a call argument of a variable's initializer: its body checked
// once the variable has its type (tsc defers function bodies), not with the variable any
declare function show(o: { on: () => void | Promise<void> }): { close(): void };
const dialog = show({ on: async () => { const n: number = dialog; void n; } });
export const d = dialog;
declare function gen<T>(o: { on: (x: T) => void; v: T }): { get(): T };
const g = gen({ v: 1, on: (x) => { const s: string = x; const m: string = g.get(); void s; void m; } });
export const gg = g;
const o = new Map([[1, () => { o.clear(); const z: number = o; void z; }]]);
export const oo = o;
