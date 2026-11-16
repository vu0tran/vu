// A distributive conditional that maps every member to itself gives back the union (its alias).
type Scope = 'a:b' | 'c:d';
type Keep<T> = T extends Function ? never : T;
declare const k: Keep<Scope>;
export const n: number = k;
declare const ks: Keep<Scope>[];
export const m: number = ks;
type Drop<T> = T extends 'a:b' ? never : T;
declare const d: Drop<Scope>;
export const o: number = d;
