declare const e2: [string, string | string[]] | undefined;
declare function isS(x: unknown): x is string;
export const a1 = isS(e2?.[1]) ? e2[1] : 1;
export const a2 = Array.isArray(e2?.[1]) ? e2[1] : 1;
export const a3 = Array.isArray(e2?.[1]) ? e2 : 1;
export const a4 = isS(e2?.[1]) ? e2 : 1;
export const a5: 'z' = isS(e2?.[1]) ? e2 : 1;
