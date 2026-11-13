class A { a = 1 }
class B { b = 2 }
class C extends A { c = 3 }
interface Mix { mix(): void }
type U = (A & Mix) | (B & Mix);
declare const u: U;
if (u instanceof A) { const n: number = u; } else { const n: number = u; }
if (u instanceof C) { const n: number = u; } else { const n: number = u; }
if (u instanceof B) { const n: number = u; }
declare const v: (C & Mix) | B;
if (v instanceof A) { const n: number = v; } else { const n: number = v; }
declare const w: A & Mix;
if (w instanceof B) { const n: number = w; } else { const n: number = w; }
export {};
