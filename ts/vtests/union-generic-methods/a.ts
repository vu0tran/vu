// a method on a union of array types: the members' generic signatures combined (same type
// parameters), their parameters intersected; instanceof with generic construct signatures
interface A { json: { a: number }; x: string }
interface B { json: { b: string }; y: number }
declare const Buf: { new(s: string): Box<string>; new<T extends object = {}>(v: T): Box<T> };
interface Box<T> { v: T }
export function f(r: A[] | B[], u: unknown) {
  const out = r.flatMap((item) => item.json);
  const n: number = out;
  const m = r.map((item) => item.json);
  const n2: number = m;
  const fl = r.filter((item) => !!item.json);
  const n3: number = fl;
  if (u instanceof Buf) { const z: number = u; }
}
