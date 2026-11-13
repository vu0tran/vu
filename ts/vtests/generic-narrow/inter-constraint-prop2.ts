type A = { k: string | number; a: 1 };
type B = { k: string; b: 2 };
function f<W extends A & B>(w: W) { const x: 'z' = w.k; return w.a + w.b; }
function g<W extends A & B>(w: W) { return w.nope; }
export { f, g };
