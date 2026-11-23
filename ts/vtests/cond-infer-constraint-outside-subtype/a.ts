type Procedure = (...args: any[]) => any;
type Params<T> = T extends (...args: infer A) => any ? A : never;
interface Ctx<T> { calls: Params<T>[] }
interface Other { calls: unknown[][]; tag: string }
declare function isOther(x: unknown): x is Other;
declare const v: Ctx<Procedure> | number;
export function f() {
  if (isOther(v)) return;
}
declare const b: Ctx<Procedure>;
export function g() {
  const [x] = b.calls[0] ?? [];
  const n: [typeof x] = 0;
}
