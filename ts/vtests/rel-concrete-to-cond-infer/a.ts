// undefined (a concrete source) to a generic conditional type with infer positions: not related,
// structuredTypeRelatedTo has no other rule for it (here in an array literal's subtype reduction,
// comparing two generic signatures' parameters)
type PV<T, P> = P extends `${infer K}.${infer R}` ? (K extends keyof T ? R : never) : P extends keyof T ? T[P] : never;
type SetV<T> = <N extends keyof T & string>(name: N, value: PV<T, N>, o?: { d: boolean }) => void;
type GetS<T> = <N extends keyof T & string>(name: N, state?: { a: T }) => boolean;
declare const sv: SetV<{ x: number }>;
declare const gs: GetS<{ x: number }>;
const arr = [gs, sv];
const len: string = arr.length;
function f<T, N extends string>(u: undefined, s: string, o: { a: 1 }) {
  const a: PV<T, N> = u;
  const b: PV<T, N> = s;
  const c: PV<T, N> = o;
}
