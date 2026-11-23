// a loop assigning a variable of an alias union: the head's `O | undefined` and `"a" | "b" |
// undefined` are the same type (settled); x! of O | undefined is O (filterType keeps the origin)
type O = 'a' | 'b';
declare function isO(x: unknown): x is O;
export function f(entries: string[]) {
  let origin: O | undefined;
  for (const key of entries) {
    origin = isO(key) ? key : undefined;
    if (!isO(origin)) throw new Error(`bad ${key}`);
  }
  if (origin! === 1) {}
}
declare let x: O | undefined;
if (x! === 1) {}
declare let y: O | null | undefined;
if (y! === 1) {}
