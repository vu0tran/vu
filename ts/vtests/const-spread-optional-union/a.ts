// a spread of X | {} or X | undefined in a const object literal: X's properties, optional and readonly;
// of several object types: the literal for each, their union
declare const input: { market?: string; first?: number };
declare const flag: boolean;
const base = {
  bounded: false,
  ...(input.market ? { market: input.market } : {}),
  surface: 'x',
} as const;
export const n: number = base;
const b2 = { a: 1, ...(flag ? { b: 'q' } : undefined) } as const;
export const m: number = b2;
const b3 = { a: 1, ...(flag ? { b: 'q' } : { c: 2 }) } as const;
export const o: number = b3;
const profiles = { dev: { url: 'a', n: 1 }, prod: { url: 'b', m: true } };
declare const env: 'dev' | 'prod';
const common = { e: env, ...profiles[env], port: 3 };
const r = { ...common, enabled: false } as const;
export const q: number = r;
