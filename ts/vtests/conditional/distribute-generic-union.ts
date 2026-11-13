type IsS<T> = T extends string ? 's' : 'n';
export function f<T>(x: T) { const z: 'z' = null as unknown as IsS<T | 1>; return z; }
