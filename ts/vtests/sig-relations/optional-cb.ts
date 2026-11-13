type A = { a: 1 }; type AB = { a: 1; b: 2 };
declare let a: (x: AB) => void;
export let b: ((x: A) => void) | undefined = a;
interface P1 { m(cb?: (x: A) => void): void }
interface P2 { m(cb: (x: AB) => void): void }
declare let p1: P1; declare let p2: P2;
p1 = p2;
interface P3 { m(cb: ((x: A) => void) | undefined): void }
declare let p3: P3;
p3 = p2;
