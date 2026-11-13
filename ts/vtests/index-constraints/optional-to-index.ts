declare const r: string | undefined;
export const body: Record<string, string> = { a: 'x', ...(r ? { resource: r } : {}) };
declare const o: { a: string; b?: string };
export const b2: Record<string, string> = o;
declare const o3: { a: string; b?: string | undefined };
export const b3: { [k: string]: string } = o3;
declare const o4: { n?: null | string }; export const b4: Record<string, string> = o4;
