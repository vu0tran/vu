// An object of index signatures only to a generic mapped type: not related.
declare const anyIdx: { [k: string]: any };
declare const strIdx: { [x: string]: string };
export function pick<M, A extends keyof M>(): Pick<M, A> {
  return anyIdx;
}
export function partial<T extends string>(): Partial<Record<T, string>> {
  return strIdx;
}
type Group = { fields: Record<string, number> };
type Values<G extends Group> = { [K in keyof G['fields']]: string | undefined };
export function values<G extends Group>(): Values<G> {
  return strIdx;
}
export function asserted<M, A extends keyof M>(): Pick<M, A> {
  return anyIdx as Pick<M, A>;
}
export function s1<T extends string>(): Record<T, string> { return strIdx; }
declare const u: unknown;
type NonNull<T extends readonly unknown[]> = { [K in keyof T]: NonNullable<T[K]> };
export function un<T extends readonly unknown[]>(): NonNull<T> {
  return u;
}
export function un2<T extends readonly unknown[]>(v: readonly [...T]): NonNull<T> {
  return v as unknown as NonNull<T>;
}
