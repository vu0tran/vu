type MP<T> = { _m: 1 } & T;
declare const mock: <T, R extends MP<T> = MP<T>>(impl?: Partial<T>) => R;
declare function mocked<T>(obj: T): ReturnType<typeof mock<T>>;
interface IC { node: string; index: number }
export const c: IC = mocked<IC>({ node: 'a', index: 1 });
export const d: 'z' = mocked<IC>({ node: 'a', index: 1 });
declare function id<T>(x: T): T;
type F = typeof id<string>;
export const f: F = (x: number) => x;
const g = id<string>;
export const h: 'z' = g;
class Box<T> { constructor(public v: T) {} }
const B = Box<number>;
export const bb: 'z' = new B(1);
