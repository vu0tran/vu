export {};
interface H { a: number }
declare function f(a: string, h?: H): void;
declare const sh: H | 'default';
const t = sh === 'default' ? [] : [sh];
f('x', ...t);
f('x', ...(true ? [] : [{ a: 1 }]));
f('x', ...(true ? [{ a: 1 }, { a: 2 }] : []));
f('x', ...(true && [{ a: 1 }]));
