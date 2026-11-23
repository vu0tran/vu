declare const s: string;
declare const t: string[];
export const z1 = [s] as string[];
export const z2 = [s, ...t] as string[];
export const z3 = [...t] as string[];
