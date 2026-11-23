// A homomorphic mapped type (Partial, Readonly) over Record<any, V> or Record<E, V> with E
// unresolved: keyof is any (or the error type), and the members come from the modifiers type's
// index signatures, forEachMappedTypePropertyKeyTypeAndIndexSignatureKeyType.
import { E } from './missing';
declare const k: E;
declare const m: Partial<Record<E, string>>;
export const x1: number = m[k];
export const x2: number = m['q'];
declare const r: Readonly<Record<E, boolean>>;
export const x3: string = r[k];
declare const m4: Partial<Record<any, string>>;
export const x4: number = m4['q'];
type P<T> = { [K in keyof T]?: T[K] };
declare const m5: P<Record<any, string>>;
export const x5: number = m5['q'];
declare const k1: keyof Record<any, string>;
export const x6: { q: 1 } = k1;
