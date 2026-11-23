export function f<T>(t: T) {
  const x: number = t as NonNullable<T | undefined>;
  return x;
}
