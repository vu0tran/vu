// spreads of unions with empty members after written properties; spreads of arrays
export {};
declare const u: { a: 1 } | { b: 2 } | undefined;
const r5 = { q: 1, ...u }; const k5: number = r5;
declare const e: { a: 1 } | { b: 2 } | null;
const r7 = { z: 1, ...e }; const k7: number = r7;
const r8 = { z: 1, ...e }; const k8: { z: number } = r8; const k9: { a: 1 } = r8;
