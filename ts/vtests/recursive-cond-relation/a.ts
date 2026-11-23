// Two instantiations of a recursive conditional (a PathValue over T[K]) related: extends types
// mentioning no type parameter the mappers give differently are one type, and the recursion
// ends as isDeeplyNestedType's Ternary.Maybe. tsc reports nothing.
type FV = Record<string, any>;
interface D extends FV { a?: string }
type PVI<T, P extends string> = T extends any ? P extends `${infer K}.${infer R}` ? K extends keyof T ? PVI<T[K], R> : never : P extends keyof T ? T[P] : never : never;
type Path<T> = keyof T & string;
type Getter<T extends FV> = {
  (): T;
  <N extends Path<T>>(name: N): PVI<T, N>;
};
declare const g: Getter<D>;
const g2: Getter<FV> = g;
type Getter2<T extends FV> = <N extends Path<T>>(name: N) => PVI<T, N>;
declare const h: Getter2<D>;
const h2: Getter2<FV> = h;
interface Ctl<T extends FV> { get: Getter<T>; v: T }
declare const c: Ctl<D>;
const c2: Ctl<FV> = c;
export const n: number = 'x';
