// inferring to a homomorphic mapped type from an intersection: its properties together
type Mutable<T> = T extends Readonly<infer U> ? U : T;
declare const c: Mutable<{ a: 1 } & { b: 2 }>;
export const c1: boolean = c;
declare function f<T>(o: { [K in keyof T]: T[K] }): T;
export const c2: boolean = f({} as { x: string } & { y: number });
