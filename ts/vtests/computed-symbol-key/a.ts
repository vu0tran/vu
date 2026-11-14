declare const s: symbol;
const o = { [Symbol.for('foo')]: 'bar', a: 1 };
const v: number = o[s];
const o3: { [k: symbol]: "a" | "b" } = { [s]: "a" };
const o4: { a: number } = { [s]: 1, a: 2 };
function f(x: unknown) { return x; }
f({ [Symbol.for('foo')]: 'bar' });
const arr: [string, unknown][] = [["x", { [Symbol.iterator]: 1 }], ["y", { [s]: 2 }]];
export {};
