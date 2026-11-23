export const x: { a: 1 } = { a: 1, b: 2 } as const;
export const y: readonly { a: 1 }[] = [{ a: 1, b: 2 }] as const;
declare function f<T>(x: readonly T[]): T;
const z = f([{ a: 1 }, { b: 'x' }] as const);
const w = [{ a: 1 }, { b: 'x' }] as const;
const q2: number = w;
export const zz: { readonly a: 1 } | { readonly b: 'x' } = z;
if ('a' in z) { const n: string = z.a; }
if (z.b !== undefined) { const m: number = z.b; }
export const y2: readonly { a: 1 }[] = [{ a: 1, b: 2 }];
export const y3: { a: 1 }[] = [{ a: 1, b: 2 }];
export const y4: [{ a: 1 }] = [{ a: 1, b: 2 }];
export const y5: readonly [{ a: 1 }] = [{ a: 1, b: 2 }] as const;
