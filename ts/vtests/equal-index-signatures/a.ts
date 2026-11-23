// Equal<X, Y> on index signatures: identical object types have both or neither of each index signature, of identical types (drizzle's ColumnsSelection).
type Equal<X, Y> = (<T>() => T extends X ? 1 : 2) extends (<T>() => T extends Y ? 1 : 2) ? true : false;
type CS = Record<string, unknown>;
declare function f<A, B>(a: A, b: B): Equal<A, B>;
declare const a1: CS;
declare const b1: { [x: string]: unknown };
declare const c1: { [x: string]: string };
declare const d1: { [x: number]: unknown };
const r1: false = f(a1, b1);
const r2: true = f(a1, c1);
const r3: true = f(b1, d1);
