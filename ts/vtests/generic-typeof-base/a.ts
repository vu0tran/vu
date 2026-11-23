// typeof narrowing of a generic whose constraint is generic too (a conditional, T[P]): its
// constraint's constraint, as getBaseConstraintOfType; === / !== "undefined" give T & undefined and
// T & ({} | null); a deferred conditional source relates through its branches (react-hook-form's
// PathValue in a package's SelectField).
type PV<T, P> = P extends keyof T ? T[P] : never;
export function f<T extends Record<string, unknown>, N extends string>(v0: PV<T, N>, key: string) {
  let value = v0;
  if (typeof value === 'object') {
    const a: number = value;
    value = (value as any)[key];
  }
  const b: number = value;
  const c: string = String(value ?? '');
}

export function f2<T extends Record<string, any>, N extends string>(value: PV<T, N>, type: string) {
  if (type === 'number' && typeof value !== 'undefined') { const a: number = value; }
  const b: number = value;
}
export function g<T>(value: T, type: string) {
  if (type === 'number' && typeof value !== 'undefined') { const a: number = value; }
  const b: number = value;
}
export function h<T>(value: T) {
  if (typeof value !== 'undefined') { const a: number = value; }
  const b: number = value;
}
