export {};
type EP<T> = T extends string[] ? { [K in `on${Capitalize<T[number]>}`]?: 1 } : never;
type W<T> = { -readonly [P in keyof T]: T[P] };
declare class ZE<T extends [string, ...string[]]> { o: T }
declare function ce<U extends string, T extends Readonly<[U, ...U[]]>>(values: T): ZE<W<T>>;
interface E<T extends any[]> { t: T }
type F<T> = E<T extends readonly [...infer A] ? A : never>;
type G<T> = E<T extends readonly (infer A)[] ? A[] : never>;
type Q = E<string>;
interface D<T extends string = "a"> { t: T }
let d1: D;
let d2: D<1>;
