export function f(a: number) { return a; }
f.label = 'x';
f.count = 1;
f.count = 2;
export const z1: 'z' = f.label;
export const z2: 'z' = f;
f.label = 3;
function g() {}
g.h = () => g.k;
g.k = 1;
export const z3: 'z' = g.h;
export function n() { function inner() {} inner.p = 1; return inner; }
export const z4: 'z' = n();
