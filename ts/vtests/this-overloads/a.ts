interface Ctx { a: number }
interface Other { b: string }
interface M {
  run(this: Ctx, x: number): number;
  run(ctx: Ctx, x: string): string;
}
declare const m: M;
declare const cm: M & Ctx;
const r1: boolean = m.run({ a: 1 }, "s");
const r2: boolean = cm.run(1);
const r3: boolean = cm.run({ a: 1 }, "s");
m.run({ a: 1 }, 1);
interface M2 { go(this: Other): number; go(this: Ctx, x: number): string; }
declare const m2: M2 & Other;
const r4: boolean = m2.go();
export {};
