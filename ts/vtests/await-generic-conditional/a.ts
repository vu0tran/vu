type Out<T> = T extends { _o: infer O } ? O : unknown;
type Out2<T> = T extends { _o: any } ? T["_o"] : never;
async function f<S extends { _o: unknown }>(p: Promise<Out<S>>, q: Out2<S>) {
  const v = await p;
  const n: unknown = v;
  const w = await q;
  const m: number = w;
}
export {};
const z: number = 'x';
type Out3<T> = T extends { _o: any } ? T["_o"] : unknown;
declare function parse<S extends { _o: unknown }>(s: S, raw: unknown): Out3<S>;
async function h<S extends { _o: unknown }>(s: S): Promise<Out3<S>> {
  return parse(s, 1);
}
async function h2<S extends { _o: unknown }>(s: S): Promise<Out3<S> | null> {
  const r = parse(s, 1);
  return r;
}
