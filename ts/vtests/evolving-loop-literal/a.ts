// an evolving array pushed an array or object literal in a loop: the same type each pass
declare function f(): Promise<number>;
declare const o: { a: number[] };
export async function g(n: number) {
  const ps = [];
  for (let i = 0; i < n; i++) {
    try {
      for (const k of o.a) { if (k) break; }
      ps.push(f());
    } catch (e) {
      if (e) {
        ps.push(Promise.resolve([{ json: {}, error: e }]));
        continue;
      }
      throw e;
    }
  }
  const r = await Promise.allSettled(ps);
  const k: boolean = r;
}
export function h(n: number, e: unknown) {
  const ps = [];
  for (let i = 0; i < n; i++) {
    ps.push(1);
    ps.push([{ error: e }]);
  }
  const k: boolean = ps;
}
