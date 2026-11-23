type Cfg = Record<string, { d?: string }>;
declare function q(v: { keys: Array<string> | string; m?: string }): { data: number };
export const g = <C extends Cfg, T extends readonly Extract<keyof C, string>[]>(flags: T, m?: string) => {
  const r = q({ keys: [...flags], ...(m ? { m } : {}) });
  const x = [...flags];
  const y: string[] = [...flags];
  const z = [1, ...flags];
  const n: number = x;
  const n2: number = z;
  return r.data;
};
export const k = <T extends readonly [string, number]>(t: T) => {
  const u = [true, ...t];
  const s: (string | number | boolean)[] = u;
  const n: number = u;
  return u;
};
export const k2 = <T extends string[]>(t: T): string[] => [...t];
const r2: number = g<{ a: {} }, ['a']>(['a']);
