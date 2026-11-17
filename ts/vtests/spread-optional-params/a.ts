export {};
interface H { a: number }
declare class R { constructor(a: string, b: number, h?: H) }
declare const sh: H | 'default';
const s = new R('x', 1, ...(sh === 'default' ? [] : [sh]));
declare function f(a: string, h?: H): void;
f('x', ...(sh === 'default' ? [] : [sh]));
