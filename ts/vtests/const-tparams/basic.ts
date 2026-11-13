function id<const T>(x: T): T { return x; }
const t = id([1, 'a']);
export const t2: readonly [1, 'a'] = t;
const o = id({ k: 'v', n: [1, 2] });
export const o2: { readonly k: 'v'; readonly n: readonly [1, 2] } = o;
export const bad: 3 = id(4);
function arr<const T extends readonly unknown[]>(x: T): T { return x; }
export const a1: readonly ['p', 'q'] = arr(['p', 'q']);
function mut<const T extends unknown[]>(x: T): T { return x; }
export const m1: ['p', 'q'] = mut(['p', 'q']);
