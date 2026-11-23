export function f<T extends Record<string, unknown>>(p: Partial<T>) {
  const a: Partial<T> = 1;
  const b: Partial<T> = "s";
  const c: Readonly<T> = 1;
  const d: Partial<T> = p;
}
export function g<T extends { [k: string]: number }>() {
  const a: Partial<T> = 1;
}
