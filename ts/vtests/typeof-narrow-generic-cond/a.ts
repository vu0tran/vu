// typeof x === 'string' with x a conditional type whose constraint isn't computed (react-hook-form's
// FieldPathValue): x & string where it's true, x where it's false
type PV<T, P> = P extends keyof T ? T[P] : never;
interface F<T, N extends keyof T> { value: PV<T, N>; name: N }
export function h<T, N extends keyof T>(p: { field: F<T, N> }) {
  const { field: { value } } = p;
  const s: string = typeof value === 'string' ? value : '';
  return s;
}
export function k<T>(x: T) {
  if (typeof x === 'string') { const r: 1 = x.length; }
}
