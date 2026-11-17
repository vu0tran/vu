export {};
interface H { a: number }
declare function f(a: string, h?: H): void;
declare function g(a: string, h: H): void;
declare function k(a: string, h?: H, i?: number): void;
declare const arr: H[];
declare const nums: number[];
f('x', ...arr);
g('x', ...arr);
f('x', ...nums);
k('x', ...arr);
