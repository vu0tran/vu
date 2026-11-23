// `${number}` reads a number index signature (an array's or tuple's elements); a literal name reads
// the template index signatures it matches; a tuple in an intersection is indexed as the tuple
type UI<T, U extends string | number> = [T] extends [Record<string | number, any>] ? T[U] : never;
type WSK<B> = { [K in `${Extract<keyof B, string | number>}`]: UI<B, K> };
export const d: WSK<[1, 2]>['1'] = 1n;
export const e: [1, 2][`${number}`] = 1n;
export const f: string[][`${number}`] = 1n;
export const i: ([true, true] & object)['0'] = 1n;
