export interface L { limit?: number; windowMs?: number }
export const mk = <T extends object>({ limit, windowMs, field }: L & { field: keyof T & string }) => ({ limit, windowMs, field });
export const mk2 = ({ limit, field }: L & { field: string }) => ({ limit, field });
export function mk3<T>({ limit, field }: L & { field: keyof T }) { return { limit, field }; }
export const t1: string = mk2({ field: "a" }).limit;
export function t2({ a, b }: { a: number } & { b?: string; a: 1 | 2 }) { const x: string = a; return b; }
export const t3: number = t2({ a: 1 });
