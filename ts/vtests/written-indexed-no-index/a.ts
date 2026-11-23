// a written indexed access type on an object type without a matching index signature: TS2537,
// the error type (any) after
export {};
interface R { id: string }
declare function load(): Promise<unknown>;
type E = NonNullable<Awaited<ReturnType<typeof load>>>[number];
declare const e: E;
const n1: number = e.anything;
type F = R[string];
declare const f: F;
const n2: number = f;
type G = { [k: string]: boolean }[number];
declare const g: G;
const n3: number = g;
