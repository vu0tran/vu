// An array of a type operator prints it in parentheses: (readonly [string, string])[],
// (readonly string[])[], (keyof T)[] (parenthesizeElementTypeOfArrayType).
declare const a: (readonly [string, string])[];
export const x: number = a;
declare const b: (readonly string[])[];
export const y: number = b;
export function f<T>(c: (keyof T)[]) {
  const z: number = c;
}
declare const d: readonly (readonly [1])[];
export const w: number = d;
