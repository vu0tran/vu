// keyof T as an array's element or an indexed access's object: parenthesized.
export function f<T extends object>(): number {
  const k = [] as (keyof T)[];
  return k;
}
export function g<T extends object>(): number {
  const k = [] as (keyof T)[][];
  return k;
}
export function h<T extends object, K extends keyof T>(): number {
  const r = {} as readonly (keyof T)[];
  return r;
}
