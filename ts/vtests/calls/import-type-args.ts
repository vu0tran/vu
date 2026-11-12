// import("x").A<T> with type arguments
const b: import('./m').Box<number> = { v: 's' };
const p: import('./m').Pair<number> = [1, 2];
const q: import('./m').NS.In<boolean> = { w: 1 };
const r: import('./m').Box = { v: 1 };
export {};
