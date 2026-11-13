export {};
interface Box<T> { v: T; get<K extends keyof T>(this: Box<T>, k: K): T[K]; map<U>(this: { v: T }, f: (t: T) => U): U }
declare const b: Box<{ a: number; s: string }>;
const r1: boolean = b.get("a");
const r2: boolean = b.map((t) => t.s);
declare function f<T>(this: T, x: number): T;
const o = { f, z: 1 };
const r3: boolean = o.f(1);
const r4: boolean = b.get<"s">("s");
