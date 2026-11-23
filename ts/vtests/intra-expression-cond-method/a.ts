declare const skip: unique symbol;
type Skip = typeof skip;
type Fn<T> = (ctx: { signal: AbortSignal }) => T | Promise<T>;
interface Opts<T> { fn?: Fn<T> | Skip; st?: (q: { data: T | undefined }) => number; }
declare function use<T = unknown>(o: Opts<T>): { data: T | undefined };
interface R { p: readonly number[]; }
declare function readR(s: AbortSignal): Promise<R>;
declare const c: boolean;
const q1 = use({ fn: c ? skip : ({ signal }) => readR(signal) });
const a1: number = q1.data;
const q2 = use({ fn: ({ signal }) => readR(signal) });
const a2: number = q2.data;
const q3 = use({ fn: c ? skip : ({ signal }) => readR(signal), st: (q) => q.data?.p.length ?? 0 });
const a3: number = q3.data;
const q4 = use({ fn: ({ signal }) => readR(signal), st: (q) => q.data?.p.length ?? 0 });
const a4: number = q4.data;
const q5 = use({ fn: c ? skip : (x: { signal: AbortSignal }) => readR(x.signal), st: (q) => q.data?.p.length ?? 0 });
const a5: number = q5.data;
const q6 = use({ fn: c ? skip : () => readR(null!), st: (q) => q.data?.p.length ?? 0 });
const a6: number = q6.data;
const q7 = use({ fn({ signal }) { return readR(signal); }, st(q) { return q.data?.p.length ?? 0; } });
const a7: number = q7.data;
const q8 = use({ fn: c ? skip : ({ signal }) => readR(signal), st(q) { return q.data?.p.length ?? 0; } });
const a8: number = q8.data;
