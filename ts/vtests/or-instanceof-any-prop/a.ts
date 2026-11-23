// a || b of instanceof narrowings on a property declared any or unknown: the union of the two,
// reduced by subtypes (RangeError goes into Error; DOMException's readonly message keeps it).
declare const signal: AbortSignal;
declare const o: { reason: any; u: unknown; n: { d: any } };
class A { a = 1 }
class B extends A { b = 2 }
const v1 = o.reason instanceof Error || o.reason instanceof DOMException ? o.reason : 0;
const n1: string = v1;
const v2 = signal.reason instanceof Error || signal.reason instanceof RangeError ? signal.reason : 0;
const n2: string = v2;
const v3 = o.u instanceof A || o.u instanceof B ? o.u : 0;
const n3: string = v3;
const v4 = o.n.d instanceof Error || o.n.d instanceof DOMException ? o.n.d : 0;
const n4: string = v4;
declare let x: any;
const v5 = x instanceof B || x instanceof A ? x : 0;
const n5: string = v5;
const v6 = !(o.reason instanceof Error) && !(o.reason instanceof DOMException) ? 0 : o.reason;
const n6: string = v6;
if (o.reason instanceof Error || o.reason instanceof DOMException) { const n7: string = o.reason; }
function g(z: any) { if (z instanceof RangeError) { } else if (z instanceof Error) { } else return; const n8: string = z; }
function h(e: unknown) { const m = e instanceof Error || e instanceof DOMException ? e.message : String(e); const n9: number = m; }
// (the join of a predicate's type and object is object; a get accessor beside a spread is mutable,
// so the literal goes into the declared type it spreads)
interface El<P> { type: string; props: P }
declare function isEl(node: object): node is El<{ title: string }>;
function k(node: unknown) {
  if (node === null || typeof node !== 'object') return;
  if (isEl(node)) node.props.title;
  const n10: number = node;
}
type Req = { id: string; ids: string[] };
declare const req: Req;
declare const fail: () => never;
for (const r of [{ ...req, get id() { return fail(); } }, req]) { const n11: number = r; }
export {};
