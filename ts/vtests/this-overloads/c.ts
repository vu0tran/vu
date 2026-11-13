interface Ctx { a: number }
interface NT { execute?(this: Ctx, r?: string): Promise<number> }
type ENT = NT & { execute: NonNullable<NT['execute']> };
declare const nt: ENT;
declare const ctx: Ctx;
async function m() {
  const v = await nt.execute.call(ctx);
  const w: string = v;
  const v2 = await nt.execute.call(ctx, "x");
  nt.execute.call(ctx, 1);
}
export {};
