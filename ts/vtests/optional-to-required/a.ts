// an optional property for a required one: not assignable, even where the types allow undefined
type SO = { s?: boolean };
export const d: SO extends Record<'s', SO['s']> ? 1 : 0 = 1n;
export const e: SO extends { s: boolean | undefined } ? 1 : 0 = 1n;
export const f: { s: boolean | undefined } extends SO ? 1 : 0 = 1n;
type RK<T extends object> = { [K in keyof T]-?: T extends Record<K, T[K]> ? K : never }[keyof T];
export const g: RK<{ a?: 1; b: 2; c: 3 | undefined }> = 1n;
