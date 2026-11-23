// A destructuring assignment counts as an assignment for markNodeAssignments: a let assigned so
// after a closure isn't narrowed inside the closure.
declare function f(): string | undefined;
declare function g(): { x: string | undefined; ys: (string | undefined)[] };
export function a1(): number {
  let x = f();
  if (x) {
    const h = () => x.length;
    ({ x } = g());
    return h();
  }
  return 0;
}
export function a2(): number {
  let y = f();
  if (y) {
    const h = () => y.length;
    [y] = g().ys;
    return h();
  }
  return 0;
}
export function a3(): number {
  let z = f();
  if (z) {
    const h = () => z.length;
    return h();
  }
  return 0;
}
