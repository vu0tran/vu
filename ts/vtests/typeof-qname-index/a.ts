// typeof a.b: an index signature answers a missing name (a mapped type over any); unknown's property is TS18046 or TS2571 and the error type.
type Client<D extends { method: object }> = {
  [P in keyof D["method"]]: D["method"][P] extends { kind: infer I } ? (request: I) => Promise<I> : never;
};
type Clients = { a: Client<any>; b: Client<any> };
declare function mk(): Clients['a'];
function g() {
  const c = mk();
  const inputs: Array<Parameters<typeof c.search>[0]> = [];
  const r: number = inputs;
  type X = typeof c.search;
  const x: X = 1;
}
declare const r: Record<string, number>;
declare const q: { [k: string]: string | boolean; a: string };
declare const n: { [k: number]: string };
type A1 = typeof r.foo;
type B = typeof q.zz;
type C = typeof q.a;
const a: A1 = "x";
const b: B = 1;
const c: C = 1;
declare function uf(): Promise<unknown>;
async function g2() {
  const response = await uf();
  const m = new Map<string, (typeof response.items)[number]>();
  type Q = typeof response.a.b;
  const x: number = m;
  let o = { p: response };
  type R = typeof o.p.z;
  const y: R = 1;
}
