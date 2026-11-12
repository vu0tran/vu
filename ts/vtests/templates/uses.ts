// Template literal types in unions (literals they match and string absorb), narrowing, members
export {};
type T = `a${string}`;
declare const x: T | 'ab' | 5;
const n1: number = x;
declare const y: T | string;
const n2: number = y;
declare const z: T;
if (typeof z === 'string') { const s: number = z; }
if (z === 'abc') { const s: number = z; }
const up = z.toUpperCase();
const sl: number = z.slice(1);
function f(p: `x${number}`) {}
f('x1'); f('y');
let lv = z;
const lw: number = lv;
const tpl = `a${z}`;
const tq: number = tpl;
const arr: T[] = ['a1', 'b'];
