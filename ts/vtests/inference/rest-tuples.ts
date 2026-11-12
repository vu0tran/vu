// A rest parameter typed as a type parameter infers a tuple of the arguments; a covariant
// inference that fits no contravariant candidate gives way to them; iterating through a
// type parameter's constraint; matchAll's iterator
export {};
declare function f<T extends unknown[]>(...args: T): T;
const r = f(1, 'a');
const n: number = r;
function g<T extends string[]>(...xs: T) { for (const x of xs) { const k: number = x; } return xs; }
declare function h<A extends any[]>(fn: (...args: A) => void, ...a: A): void;
h((x: number, y: string) => {}, 1, 'a');
h((x: number) => {}, 's');
declare function hh2<A>(fn: (a: A) => void, a: A): void;
hh2((x: number) => {}, 's');
declare function hh<A extends any[]>(fn: (...args: A) => void, ...a: A): void;
hh((x: number) => {}, 's');
const mm = 'aXbX'.matchAll(/X/g);
for (const r of mm) { const k: number = r; }
