interface Base<T> { base: T; }
interface Assertion<R, T> extends Base<T> { not: Assertion<R, T>; toBe(v: T): R; }
export type { Assertion };
export declare const expect: <T>(v: T) => Assertion<void, T>;
