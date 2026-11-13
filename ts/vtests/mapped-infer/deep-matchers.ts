declare abstract class AM<S> { protected sample: S; abstract asymmetricMatch(other: unknown): boolean; }
type W<T> = T | AM<unknown>;
type D<T> = T extends Array<infer E> ? W<T> | D<E>[] : T extends object ? W<T> | { [K in keyof T]: D<T[K]> } : W<T>;
declare const ac: <T = unknown>(expected: Array<D<T>>) => any;
export const a = ac(['create', 'read']);
export const b = ac([1, { x: 'y' }]);
export const c: 'z' = ac;
