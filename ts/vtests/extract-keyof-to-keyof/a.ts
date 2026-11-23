// Extract<keyof E, string> to keyof E, E constrained by a record over its own keys: its default
// constraint keyof E & string has the target.
export type NumberEnum<E> = Record<Extract<keyof E, string>, number>;
export type EnumKey<E> = Extract<keyof E, string>;
export function f<E extends NumberEnum<E>>(e: E, k: EnumKey<E>): number {
  const key: keyof E = k;
  const n: string = e[key];
  return e[k];
}
