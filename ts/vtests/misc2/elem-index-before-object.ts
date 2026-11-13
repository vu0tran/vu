interface C { [k: string]: { main: number[] } }
declare const c: C;
export const a: 'z' = c['constructor'];
export const b: 'z' = c.constructor;
export const d: 'z' = c['toString'];
declare const r: Record<string, { main: 1 }>;
export const e: 'z' = r['constructor'];
