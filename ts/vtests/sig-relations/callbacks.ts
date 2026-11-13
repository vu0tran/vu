type A = { a: 1 }; type AB = { a: 1; b: 2 };
declare let f1: (cb: (x: A) => void) => void;
declare let f2: (cb: (x: AB) => void) => void;
f1 = f2; f2 = f1;
declare let g1: (cb: (x: A) => A) => void;
declare let g2: (cb: (x: A) => AB) => void;
g1 = g2; g2 = g1;
interface M1 { m(cb: (x: A) => A): void }
interface M2 { m(cb: (x: AB) => AB): void }
declare let m1: M1; declare let m2: M2;
m1 = m2; m2 = m1;
interface P1 { m(cb?: (x: A) => void): void }
interface P2 { m(cb: (x: AB) => void): void }
declare let p1: P1; declare let p2: P2;
p1 = p2; p2 = p1;
declare let h1: (cb: (x: string) => void) => void;
declare let h2: (cb: (x: number) => void) => void;
h1 = h2;
interface Q1 { m(cb: (x: string) => void): void }
interface Q2 { m(cb: (x: number) => void): void }
declare let q1: Q1; declare let q2: Q2;
q1 = q2;
interface R1 { m(cb: (x: string) => string): void }
interface R2 { m(cb: (x: string) => number): void }
declare let r1: R1; declare let r2: R2;
r1 = r2;
export {};
