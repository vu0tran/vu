declare const t1: readonly [number, ...string[]];
declare const t2: [number, string?];
declare const t3: [boolean, ...number[], string];
const a1 = [...t1];
const a2 = [...t2];
const a3 = ['x', ...t3];
const n1: boolean = a1;
const n2: boolean = a2;
const n3: boolean = a3;
function f(...args: [string, number?]) { const xs: unknown[][] = []; xs.push(['a', ...args]); const q: boolean = ['a', ...args]; }
export {};
