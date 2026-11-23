// T & P with T's constraint all primitives is a constrained type variable (getIntersectionType),
// and a union of them whose P cover the constraint is T (removeConstrainedTypeVariables): the
// mapped type below is indexed by S, not (S & RS.A) | (S & RS.B) | (S & RS.C).
enum RS { A = "a", B = "b", C = "c" }
type RR = { status: RS.A } | { status: RS.B; sentAt: string | null } | { status: RS.C; expiredAt: string };
type Of<S extends RS> = Extract<RR, { status: S }>;
const D: { [S in RS]: (r: Of<S>) => string } = {
  [RS.A]: () => "a",
  [RS.B]: ({ sentAt }) => sentAt ?? "",
  [RS.C]: ({ expiredAt }) => expiredAt,
};
function describe<S extends RS>(r: Of<S>): string {
  const d: (r: Of<S>) => string = D[r.status];
  const n: number = d;
  return d(r);
}
function f<S extends RS>(w: ({ status: S } & RR)) {
  type Q1 = (S & RS.A) | (S & RS.B) | (S & RS.C);
  const a: { x: number } = null! as { x: Q1 };
  const st = w.status;
  const b: { x: number } = null! as { x: typeof st };
  type Q3 = (S & "a") | (S & "q");
  const c: { x: number } = null! as { x: Q3 };
  type Q4 = (S & RS.A) | (S & RS.B);
  const d: { x: number } = null! as { x: Q4 };
  type Q5 = (S & RS.A) | (S & RS.B) | (S & RS.C) | number;
  const e: { x: boolean } = null! as { x: Q5 };
}
function g<S extends "a" | "b">(x: (S & "a") | (S & "b"), y: S & string, z: S & "a", u: S & number) {
  const c: { x: number } = null! as { x: typeof x };
  const c2: { x: number } = null! as { x: typeof y };
  const c3: { x: number } = null! as { x: typeof z };
  const c4: { x: number } = null! as { x: typeof u };
}
function i<T extends string | number>(x: (T & string) | (T & number), y: T & {}) {
  const c: { x: boolean } = null! as { x: typeof x };
  const d: { x: boolean } = null! as { x: typeof y };
}
export {};
