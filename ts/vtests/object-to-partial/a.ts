// object to a mapped type with ?, made over its keys (Partial<Record<string, T>>): related.
declare const o: object;
export const a: Record<string, number | undefined> = o;
export const b: Record<string, number> = o;
export const c: { [k: string]: unknown } = o;
export const d: { x?: number } = o;
export const e: Partial<Record<string, number>> = o;
