type W<T> = { -readonly [P in keyof T]: T[P] };
declare class ZE<T extends [string, ...string[]]> { o: T }
declare function ce<U extends string, T extends Readonly<[U, ...U[]]>>(values: T): ZE<W<T>>;
declare function ce<U extends string, T extends [U, ...U[]]>(values: T): ZE<T>;
export const e: ZE<['https', 'http']> = ce(['https', 'http']);
declare function c2<U extends string, T extends [U, ...U[]]>(values: T): T;
export const e2: 'z' = c2(['a', 'b']);
declare function c3<U extends string, T extends readonly [U, ...U[]]>(values: T): T;
export const e3: 'z' = c3(['a', 'b']);
