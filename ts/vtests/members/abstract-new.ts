type AC<T = unknown> = abstract new (...args: unknown[]) => T;
type CC<T = unknown> = new (...args: unknown[]) => T;
abstract class A { x = 1; }
class B extends A {}
export const a1: AC<A> = A;
export const a2: AC<A> = B;
export const a3: CC<A> = A;
declare const ac: AC<A>;
export const a4 = new ac();
export const a5: CC<A> = ac;
export function make<T>(k: AC<T>): T { return null as unknown as T; }
export const a6: number = make(A);
