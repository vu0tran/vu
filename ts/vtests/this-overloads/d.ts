interface Ctx { a: number }
declare const g: (this: Ctx, x: string) => number;
declare const h: (x: string, y: number) => boolean;
declare const ctx: Ctx;
const r1: string = g.apply(ctx, ["s"]);
const r2: string = h.apply(null, ["s", 1]);
h.apply(null, ["s", "t"]);
const b1 = g.bind(ctx);
const r3: string = b1("s");
const b2 = h.bind(null, "s");
const r4: string = b2(1);
const b3 = h.bind(null);
const r5: string = b3("s", 2);
function k(this: Ctx, ...args: unknown[]) { return g.apply(this, args as [string]); }
const r6: string = k.call(ctx);
class C { m(x: number) { return x; } f = this.m.bind(this); }
const r7: string = new C().f(1);
export {};
