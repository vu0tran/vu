type IsOpt<T extends object, K extends keyof T> = K extends keyof T ? T extends Record<K, T[K]> ? false : true : false;
type OptKeys<T extends object> = keyof { [K in keyof T as IsOpt<T, K> extends false ? never : K]: never } & keyof T;
const a: 'q' = null as unknown as OptKeys<[true, false]>;
const b: 'q' = null as unknown as OptKeys<{ a?: 1; b: 2 }>;
type Coll<T> = T extends readonly [(infer F)?, ...infer R] ? [F, R] : 0;
const c: 'q' = null as unknown as Coll<[1, 2]>;
export {};
export {};
