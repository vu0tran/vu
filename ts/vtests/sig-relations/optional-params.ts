export let f: (x?: number) => void = (x: number) => {};
type A = { a: 1 }; type AB = { a: 1; b: 2 };
export let g: (x?: (y: A) => void) => void = (x: (y: AB) => void) => {};
export let h: (x?: A) => void = (x: AB) => {};
export let k: (x: A | undefined) => void = (x: A) => {};
interface I1 { m(x?: A): void } interface I2 { m(x: AB): void }
declare let i1: I1; declare let i2: I2; i1 = i2;
