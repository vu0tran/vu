// spreading arrays into object literals: Array's members, related to arrays
export {};
interface A { length: number; [n: number]: string }
const o = { length: 1, x: true };
const a: A = o;
interface B { m(): this; length: number }
declare const bb: B;
const o2 = { ...bb };
const b2: B = o2;
const b3: number = o2;
