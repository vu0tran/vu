export {};
const m1 = new Map([['a', { s: 'x' as const }], ['b', { s: 'y' as const, e: 'z' }]]);
const m2 = new Map([['a', { s: 'x' }], ['b', { s: 'y', e: 'z' }]]);
const m3 = new Map([['a', { s: 1 }], ['b', { s: 2 }]]);
declare function g<K, V>(a: readonly (readonly [K, V])[]): V;
g([['a', { s: 'x' }], ['b', { s: 'y', e: 'z' }]]);
