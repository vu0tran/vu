// strict false: optional and nullable types lose undefined and null (no-unnecessary-boolean-literal-compare),
// implicit any parameters flow into unsafe uses
type Opts = { on?: boolean; flag: boolean | null; name?: string };
export function f(o: Opts, p) {
  if (o.on === true) return p.x;
  if (o.flag === false) return 1;
  const n = o.name!;
  const q = p.call();
  return n + q;
}
export const fc = (a: number) => a;
export const z = fc.call(null, 1);
