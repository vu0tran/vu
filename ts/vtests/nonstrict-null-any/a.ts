// strict: false (no strictNullChecks, no noImplicitAny)
declare function loadJson<T>(p: string, d: T): T;
declare function restore(s: { a: number }): number;
declare function id<T>(a: T): T;
declare const k: string | null;
declare const u: unknown;

// an inferred null or undefined widens to any
const r = loadJson("x", null);
const r2 = id(undefined);
const t1: typeof r = { s: 1 };
const t2: typeof r2 = { s: 1 };
restore(loadJson("x", null));
const later = Promise.resolve(1).then(() => null);
const t3: typeof later = Promise.resolve({ s: 1 });

// a && b: b's base type's falsy part, not a's
const b = k && 1 > 0;
const t4: typeof b = { s: 1 };
const c = k && "abc";
const t5: typeof c = { s: 1 };

// null | undefined alone is null
const n = Math.random() ? null : undefined;
const t6: typeof n = { s: 1 };

// unknown's apparent type is {}
const ua: {} = u;
const ub: { a: number } = u;
const uc = u.toString();
const t7: typeof uc = { s: 1 };
const ud = u.foo;
const ue = u["valueOf"];
const uf = u * 2;

// no contextual signature from several (getIntersectedSignatures without noImplicitAny)
const groups = [["a", "b"], ["c"]] as const;
groups.forEach((g) => g.some((x) => { const q: number = x; return q > 0; }));

// const x = [] is any[], not evolving
export function rooms(d: { x: number }) {
  const out = [];
  if (d.x) out.push(1);
  const q: { s: 1 }[] = out;
  return q;
}
export { t1, t2, t3, t4, t5, t6, ua, ub, ud, ue, uf };

// unknown to a union with an object type: as {}; truthy unknown stays unknown
const uu: { errors?: unknown } | string = u;
export function thrown(failure: unknown) {
  if (failure) { const z: number = failure; return z; }
  return uu;
}
