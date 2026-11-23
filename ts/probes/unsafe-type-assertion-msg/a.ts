declare const u: unknown;
declare const s: string | number;
export const a = u as any;
export const b = s as string;
export const c = (1 as any) as string;
