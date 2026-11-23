// Two variadic tuples of one shape related element by element (react-hook-form's
// UseFormGetValues overload over readonly [...TFieldNames]).
export function f<A extends string[], B extends string[]>(x: readonly [...A], y: [...A, number], z: [...B]) {
  const p: readonly [...A] = x;
  const q: [...A, number] = y;
  const r: [...A] = z;
  const s2: [...A] = x;
}
