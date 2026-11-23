// x || {} with x an intersection of object types: the intersection isn't a subtype of the fresh
// {} (as an interface isn't), so destructuring reads its properties, undefined from {}. Once
// widened (a declaration's type), {} is no longer fresh and the union reduces to it.
interface Base { key: string }
type G1 = Base & { next?: Base };
declare const gs: G1[];
const cur = gs.find((g) => g.key === "x");
const { next: n1, key: k1 } = cur || {};
const a: number = n1;
const a2: number = k1;
interface O { a?: boolean }
type G2<T extends O> = Base & (true extends T['a'] ? { c: string } : { c?: string }) & { next?: Base };
declare const gs2: G2<{ a: true }>[];
const { next: n2 } = gs2.find((g) => g.key === "x") || {};
const b: number = n2;
declare const t2: (Base & { z: number }) | null;
const { z } = t2 ?? {};
const n6: string = z;
const e2 = t2 ?? {};
const n5: number = e2;
declare const s: string | undefined;
const e1 = s || {};
const n4: number = e1;
const { y } = {};
declare const t4: { q: 1 } & { r: 2 } | undefined;
const { q } = t4 || {};
const n9: string = q;
