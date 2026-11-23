// a context-sensitive literal with a spread against overloads: the spread's properties count, so
// Object.freeze's T extends Function overload doesn't fit and the callbacks get Readonly<T>'s context
type Repo = { find(owner: string, n: number): number };
declare function fz<T extends Function>(f: T): T;
declare function fz<T>(o: T): Readonly<T>;
declare const e2: { admin: number };
export const r3: Repo = fz({ ...e2, find: (owner, n) => { const s: number = owner; return n; } });
export const r5: Repo = fz({ find: (owner, n) => { const s: number = owner; return n; }, ...e2 });
declare function gz<T extends Function>(f: T): T;
declare function gz<T>(o: T): T;
export const r6: Repo = gz({ ...e2, find: (owner, n) => { const s: number = owner; return n; } });
export function make(extra?: boolean): Repo {
  return Object.freeze({
    ...(extra === undefined ? {} : { admin: 1 }),
    find: (owner, n) => { const s: number = owner; return n; },
  });
}
