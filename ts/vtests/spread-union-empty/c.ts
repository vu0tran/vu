declare const u: { a: string } | { b: number };
export const z: number = { ...u };
declare const v: { a?: undefined; b?: undefined } | { a: string; b: string } | { a: string; b?: undefined };
export const z2: number = { ...v };
