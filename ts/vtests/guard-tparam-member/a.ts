// x is T where T is one of x's members, the others concrete: T when true, the others when false
// (a package's assertHasValue: hasValue<T>(value: T | null | undefined): value is T)
declare function hasValue<T>(value: T | null | undefined): value is T;
export function f<T>(value: T | null | undefined) {
  if (hasValue(value)) return [value];
  return [value, `x ${String(value)}`] as const;
}
export function g<T>(value: T | null | undefined) {
  if (!hasValue(value)) return [value];
  return [value];
}
export const a: number = f<string>;
export const b: number = g<string>;
