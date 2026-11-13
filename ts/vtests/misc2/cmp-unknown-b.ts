export {};
declare const u: unknown;
const a = u as string;
const b = { x: u } as { x: number };
const c = [u] as number[];
const d = { x: 1 } as { x: string };
const e = (() => u) as () => number;
