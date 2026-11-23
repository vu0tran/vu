// an optional element access of a generic mapped type by a generic key: T[K] read where its
// constraint is substituted is the template at K (getSimplifiedType before the base constraint)
type M<T extends string> = { [K in T]: string };

export function f<T extends string>(cols: Record<T, boolean>, d: Partial<Record<T, string>> | undefined, key: T) {
  const r = d?.[key];
  const ok = !!r;
  const n: number = r;
  const c: string = cols[key];
  if (r !== undefined) {
    const s: string = r;
    const o: { x?: string } = { ...(r === undefined ? {} : { x: r }) };
    const b: number = r;
  }
  return ok;
}

export function g<T extends string>(d: Partial<M<T>> | undefined, e: Record<T, number> | undefined, key: T) {
  const r = d?.[key];
  const s: string | undefined = r;
  const t: string = r;
  const o: { x?: string } = { ...(r === undefined ? {} : { x: r }) };
  const q = e?.[key];
  const w: string = q;
  const z: number | undefined = q;
  const v: number = d![key];
}
