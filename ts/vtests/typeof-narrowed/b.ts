function f1(a: string | number): typeof a { return true as any; }
const r1: boolean = f1(1);
function f2(x: string | number) {
  if (typeof x === "string") {
    const g = (y: typeof x) => y;
    const r: number = g("a");
    type T = typeof x;
    const t: T = 1;
  }
  let z: string | number = 1;
  const w: typeof z = "s";
  z = "a";
  const w2: typeof z = 1;
}
function f3(o: { p: string | undefined }) {
  if (o.p) { const q: typeof o.p = undefined; }
}
export {};
