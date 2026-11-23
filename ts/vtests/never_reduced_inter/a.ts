// getReducedType: a union member that's an intersection whose shared discriminant property has
// conflicting unit types ({ ok: false } & { ok: true }) is never, so it has no properties to lack.
interface TableAssignee { a: string }
export type LeaseSyncResult =
  | { ok: true; claimed?: string }
  | { ok: false; code: 'TABLE_ALREADY_BOUND'; holder: TableAssignee }
  | { ok: false; code: 'TABLE_REGISTRY_UNAVAILABLE' };
export function f(sync: LeaseSyncResult & { ok: true }, s2: LeaseSyncResult & { ok: false }) {
  const n: number = sync.claimed;
  const m: number = s2.code;
  if (s2.code === 'TABLE_ALREADY_BOUND') { const h: number = s2.holder; }
}
type V = { kind: 1; c: string } | { kind: 2; d: number } | { kind: 2 | 3; e: boolean };
export function g(a: V & { kind: 1 }) {
  const n: number = a.c;
}
// (an optional discriminant in both: not reduced)
export function h(a: ({ k?: 1; c: string } | { k?: 2; d: number }) & { k?: 1 }) {
  const n: number = a.c;
}
