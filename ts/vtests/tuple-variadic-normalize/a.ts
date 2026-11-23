// ...R[1] and ...infer U are variadic, not rest elements (no TS1265); a variadic element after an
// optional one isn't a required element (no TS1257)
type V<A extends readonly unknown[], B extends readonly unknown[]> = [A, B] extends infer R extends [readonly unknown[], readonly unknown[]]
  ? R[0] extends [...R[1], ...infer Remain extends readonly unknown[]] ? Remain : false
  : never;
export const x: V<[1, 2, 3], [1]> = 1;
export const y: V<[1], [1, 2]> = 1;
type F<T extends readonly unknown[]> = T extends readonly [(infer First)?, ...infer Rest] ? [First, Rest] : 0;
export const f: F<[1, 2]> = 1;
// a union or never spliced into a variadic element distributes
type W<T extends unknown[]> = [...T, 1];
export const z: W<[2] | [3, 4]> = 1;
export const w: W<never> = 1;
// elements after the first rest element fold into it
type Fold<A extends unknown[], B extends unknown[]> = [...A, ...B];
export const fo: Fold<string[], number[]> = 1;
export const fo2: Fold<[1], [...string[], 2]> = 1;
