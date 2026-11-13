declare const u: unknown;
u?.toString();
declare const p: { [k: string]: unknown };
declare const k: string;
p[k]?.toString();
p.x?.toString();
export {};
