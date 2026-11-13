declare const c: { a: 1 };
export const a1: 'z' = [c, {}];
export const a2: 'z' = true ? c : {};
declare const d: { a: 1 } | undefined;
export const a3: 'z' = d ?? {};
