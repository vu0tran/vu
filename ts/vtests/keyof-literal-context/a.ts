type V = { a: string; b: string[]; c: number };
declare const v: V;
// keyof F as a literal context
declare function w4<F, T extends readonly (keyof F)[]>(f: F, name: T): T;
const z4: number = w4(v, ['b', 'a']);
// the return mapper leaves F generic in T's constraint
declare function w3<F, T extends readonly (keyof F)[]>(f: F, name: readonly [...T]): T;
const z3: number = w3(v, ['b', 'a']);
declare function w6<F, T extends readonly (keyof F)[]>(f: F, name: [...T]): T;
const z6: number = w6(v, ['b']);
// a conditional whose true branch is a conditional, over the constraint
type PI<T> = T extends readonly any[] ? never : { [K in keyof T]-?: `${K & string}` }[keyof T];
type P<T> = T extends any ? PI<T> : never;
declare function w7<F extends Record<string, any>, T extends readonly P<F>[]>(f: F, name: readonly [...T]): T;
const z7: number = w7(v, ['b', 'a']);
function h<F extends Record<string, any>, N extends readonly P<F>[]>(n: N[number]) { const y: string = n; const q: `${string}` = n; }
