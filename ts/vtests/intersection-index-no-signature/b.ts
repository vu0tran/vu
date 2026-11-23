interface A { a: number }
interface B { b: string }
declare const o: A;
declare const io: A & B;
declare const k: string;
const v1 = o[k];
const v2 = io[k];
const n1: number = null! as (A & B)[string];
export function f(w: Window & typeof globalThis, l: string) {
  // @ts-ignore
  w[l] = w[l] || [];
}
