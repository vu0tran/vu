// A literal argument whose parameter type is a literal context (a literal of its kind, keyof, a
// template literal in it) is regular, so the type parameter inferred from it keeps the literal.
type M = { a: [number]; b: [string] };
declare function on1<K>(k: K | keyof M, l: (x: K) => void): void;
on1("a", (x) => { const n: "b" = x; });
declare function on2<K>(k: K | keyof M, l: K extends keyof M ? (...a: M[K]) => void : never): void;
on2("a", (x) => { const n: string = x; });
declare function on3<K>(k: K, l: K extends keyof M ? (...a: M[K]) => void : never): void;
on3("a", (x) => { const n: string = x; });
declare function on4<K>(k: K | keyof M, l: (x: K) => void): void;
on4("zz", (x) => { const n: "b" = x; });
declare function on5<K>(k: K | number, l: (x: K) => void): void;
on5("zz", (x) => { const n: "b" = x; });
declare function on6<K>(k: K | "q", l: (x: K) => void): void;
on6("zz", (x) => { const n: "b" = x; });
declare function on7<K>(k: K | `p${string}`, l: (x: K) => void): void;
on7("zz", (x) => { const n: "b" = x; });
declare function on8<K>(k: K | string, l: (x: K) => void): void;
on8("zz", (x) => { const n: "b" = x; });
declare function on9<K>(k: K | keyof M): K;
const r9 = on9("zz"); const n9: "b" = r9;
declare function on10<K>(k: K | keyof M): K[];
const r10 = on10("zz"); const n10: "b" = r10[0];
declare function on11<K>(k: K | 5): K[];
const r11 = on11(7); const n11: "b" = r11[0];
declare function on12<K>(k: K | 5): K[];
const r12 = on12("x"); const n12: "b" = r12[0];
declare function on14<K extends string>(k: K | keyof M): K[];
const r14 = on14("zz"); const n14: "b" = r14[0];
declare function b1<K>(k: K | true, l: (x: K) => void): void;
b1(false, (x) => { const n: "b" = x; });
declare function b2<K>(k: K | 1n, l: (x: K) => void): void;
b2(2n, (x) => { const n: "b" = x; });
declare function b4<K>(k: K | "a"): { v: K };
let r4 = b4("q"); r4 = { v: "zz" };
declare function b5<K>(o: { k: K | "a" }): K[];
const r5 = b5({ k: "q" }); const n5: "b" = r5[0];
declare function b6<K>(k: [K | "a"]): K[];
const r6 = b6(["q"]); const n6: "b" = r6[0];
declare function b7<K, V>(k: K | keyof V, v: V): K[];
const r7 = b7("q", { a: 1 }); const n7: "b" = r7[0];
declare function b8<K>(...k: (K | "a")[]): K[];
const r8 = b8("q"); const n8: "b" = r8[0];
declare function b9<K>(k?: K | "a"): K[];
const r9b = b9("q"); const n9b: "b" = r9b[0];
interface Em<T> { on<K>(k: K | keyof T, l: K extends keyof T ? T[K] extends unknown[] ? (...a: T[K]) => void : never : never): void }
declare const em: Em<{ error: [err: Error, n: number] }>;
em.on("error", (err, n) => { const s: string = err; const t: string = n; });
// (a generic class's method: its type parameter's constraint through the class's arguments)
type Input<S, I = any> = (S extends string ? string : never) | I | { id: S };
declare class Base<S = number, I = any> { invoke<T extends Input<S, I>>(input: T): Promise<T>; }
declare class A extends Base<string> {}
declare class B extends Base<string, "u" | { id: 1 }> {}
declare const ca: A;
declare const cb: B;
export const c1: number = ca.invoke("x");
export const c2: number = cb.invoke("x");
