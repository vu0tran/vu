export {};
type OptKeys<T extends object> = { [k in keyof T]: undefined extends T[k] ? k : never }[keyof T];
type R<T extends object> = { [k in OptKeys<T>]?: T[k] } & { [k in Exclude<keyof T, OptKeys<T>>]: T[k] };
function f<T extends object>(t: T): R<T> { return null!; }
const r = f({ a: 1, b: undefined as number | undefined });
const b: boolean = r;
type U<X, Y> = X extends Y ? 1 : 2;
function g<Y>(y: Y) { const u: U<string, Y> = null!; const b2: boolean = u; }
const k: OptKeys<{ x?: number; y: string }> = "x";
const k2: boolean = k;
