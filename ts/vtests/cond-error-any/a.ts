import { mk } from 'nonexistent-module-x';
declare function mergeConfig<D extends Record<string, any>>(defaults: D extends Function ? never : D): Record<string, any>;
export const r = mergeConfig(mk());
type C2<T> = T extends Function ? never : T;
export const c3: C2<typeof mk> = 1;
type C4<T> = T extends string ? 1 : 2;
export const c4: C4<typeof mk> = 3;
