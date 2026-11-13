export {};
declare const r4: Partial<X>;
declare const r5: { [K in keyof X]: 1 };
declare const r6: { [K in "aa"]: 1 };
const a4: boolean = { dd: 2, ...r4, cc: 1 };
const a5: boolean = { dd: 2, ...r5, cc: 1 };
const a6: boolean = { dd: 2, ...r6, cc: 1 };
interface X { aa: 1 }
