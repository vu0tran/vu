// A type parameter member of an intersection contextual type gives its constraint's property type, a
// literal context (zod-mini's omit: mask: M & Record<Exclude<keyof M, keyof T["shape"]>, never>).
type Mask<Keys extends PropertyKey> = { [K in Keys]?: true };
declare const s: { rate: number; payment: number };
declare const o: { shape: { rate: number; payment: number } };
declare function p1<T extends Record<string, any>, M extends Mask<keyof T>>(schema: T, mask: M & Record<Exclude<keyof M, keyof T>, never>): M;
const x1: number = p1(s, { payment: true });
declare function p2<T extends { shape: Record<string, any> }, M extends Mask<keyof T["shape"]>>(schema: T, mask: M & Record<Exclude<keyof M, keyof T["shape"]>, never>): M;
const x2: number = p2(o, { payment: true });
declare function q3<T, M extends Mask<keyof T>>(schema: T, mask: M & {}): M;
const x3: number = q3(s, { payment: true });
type Omit2<T, K> = Pick<T, Exclude<keyof T, K>>;
type Identity<T> = T;
type Flatten<T> = Identity<{ [k in keyof T]: T[k] }>;
interface Obj<S extends Readonly<{ [k: string]: unknown }> = Record<string, any>> { shape: S }
declare function omit<T extends Obj, M extends Mask<keyof T["shape"]>>(schema: T, mask: M & Record<Exclude<keyof M, keyof T["shape"]>, never>): Obj<Flatten<Omit2<T["shape"], keyof M>>>;
declare const z: Obj<{ rate: number; payment: number }>;
const x4: number = omit(z, { payment: true }).shape;
