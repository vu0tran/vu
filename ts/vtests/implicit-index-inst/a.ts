export {};
function pf2<R>(rule: R) { return { r: rule }; }
const q2: { [k: string]: number } = pf2(1);
const q2b: { [k: string]: string } = pf2(1);
function pf3<R>(rule: R) { const o = { r: rule, s: 1 }; return o; }
const q3: { [k: string]: number } = pf3(1);
interface I { r: number }
function pf4<R>(rule: R): I { return { r: 1 }; }
const q4: { [k: string]: number } = pf4(1);
type T<R> = { r: R };
declare function pf5<R>(r: R): T<R>;
const q5: { [k: string]: number } = pf5(1);
const f1: { [k: string]: number } = { a: 1 } as { (): void; a: number };
const f2: { [k: string]: unknown } = (() => {}) as () => void;
declare const fx: { (): void; a: number };
const f3: { [k: string]: number } = fx;
function pf6<R>(r: R) { return { [Symbol.iterator]: r, a: 1 }; }
const f4: { [k: number]: number } = { 0: 1, a: "x" };
declare function pf7<R>(r: R): { a: R; 1: R };
const f5: { [k: number]: string } = pf7(1);
