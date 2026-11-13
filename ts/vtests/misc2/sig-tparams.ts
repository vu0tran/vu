export {};
declare function g2<T extends { q: 1 }>(this: T): T;
declare function h2<T extends { q: 1 }>(x: T): T;
const z: boolean = g2;
const z2: boolean = h2;
const z3: boolean = { g: g2 };
declare function k2<T extends string = "a", U = T[]>(x: T, y?: U): U;
const z4: boolean = k2;
class Q<T> { m<U extends T>(u: U): U { return u; } }
const z5: boolean = new Q<number>().m;
