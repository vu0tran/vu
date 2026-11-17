// globalThis as an argument: typeof globalThis (inferred into SpyOnMethodKey<T, K>).
type Procedure = (...args: any[]) => any;
type Constructable = new (...args: any[]) => any;
type SpyOnValue<T extends object, K extends keyof any> = K extends keyof Required<T> ? Required<T>[K] : (T & Record<K, unknown>)[K];
type SpyOnMethodKey<T extends object, K extends keyof any> = SpyOnValue<T, K> extends Constructable | Procedure ? K : never;
declare function idT<T extends object>(x: T): SpyOnMethodKey<T, 'setTimeout'>;
export const q: number = idT(globalThis);
declare function sp4<T extends object, K extends keyof any>(object: T, key: SpyOnMethodKey<T, K>): K;
export const a: number = sp4(globalThis, 'setTimeout');
declare const o: { setTimeout: typeof setTimeout };
export const a2: number = sp4(o, 'setTimeout');
