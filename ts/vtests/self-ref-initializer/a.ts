export {};
const a = () => { const q: number = a; };
const b = (n: number): number => n > 0 ? b(n - 1) : 0;
const c = (n: number) => { if (n > 0) return c(n - 1); return 0; };
const d = function (x: string) { const z: string = d; };
let e = () => { e = () => {}; };
const f = (n: number) => { const r = f(n); return 1; };
