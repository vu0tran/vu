// a function whose contextual type intersects a type parameter with a function type (Pothos's
// resolveType): an unconstrained type parameter has no signatures, the function type's is the one
export {};
interface Opts<M, R> { members: M[]; resolveType?: R & ((parent: M, n: number) => string) }
declare function unionType<M, R>(o: Opts<M, R>): R;
const r = unionType({ members: [{ a: 1 }], resolveType: (parent, n) => { const x: string = parent; return String(n); } });
const k: number = r;
interface Opts2<M, R extends { (p: M): string }> { resolveType: R & ((parent: M) => string) }
declare function u2<M, R extends { (p: M): string }>(m: M, o: Opts2<M, R>): R;
const r2 = u2(1, { resolveType: (p) => { const y: string = p; return ''; } });
export function inner<R, C extends object>() {
  const o: Opts<{ b: string }, R> = { members: [], resolveType: ((parent, n) => { const z: number = parent; return ''; }) as R & ((parent: { b: string }, n: number) => string) };
  const f: R & ((p: string) => number) = ((p) => { const w: boolean = p; return 1; }) as any;
  const g: C & ((p: string) => number) = (p) => { const w: boolean = p; return 1; };
  return [o, f, g];
}
