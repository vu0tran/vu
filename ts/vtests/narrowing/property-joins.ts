// Properties assigned in if/else branches join as variables do (the union of the branches' types)
export {};
interface O { p: string | number | undefined; n: { d: boolean | string } }
declare const o: O;
declare const c1: boolean;
function f1() {
  if (typeof o.p === 'string') {
    if (c1) o.p = 1;
    const a: boolean = o.p;
  }
  const b: boolean = o.p;
}
function f2() {
  o.n.d = true;
  if (c1) { o.n.d = 'x'; }
  const a: number = o.n.d;
  o.n = { d: false };
  const b: number = o.n.d;
}
function f3() {
  o.p = 'a';
  if (c1) { o.p = undefined; return; }
  const a: boolean = o.p;
}
function f4(x: O) {
  if (x.p === undefined) { x.p = 0; }
  const a: boolean = x.p;
}
function f5(x: O) {
  if (c1) { x.p = 0; } else if (Math.random()) { x.p = 'q'; }
  const a: boolean = x.p;
}
declare const o2: O; o2.p = 1;
if (c1) { o2.p = "s"; } else { o2.p = 2; }
const n1: boolean = o2.p;


class K2 { v: string | undefined; m(c: boolean) { if (c) this.v = 'a'; else this.v = 'b'; const z: number = this.v; } }
