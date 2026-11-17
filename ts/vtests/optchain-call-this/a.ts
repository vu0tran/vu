// x.m?.call(...): the receiver of call isn't undefined
interface Ctx { a: number }
interface NT { execute?(this: Ctx): Promise<string[] | null>; run(this: Ctx, x: number): number }
export async function f(nt: NT, c: Ctx, o: { nt?: NT }) {
  const r = await nt.execute?.call(c);
  const n: number = r;
  const r2 = nt.run.call(c, 1);
  const n2: string = r2;
  const r3 = await o.nt?.execute?.call(c);
  const n3: number = r3;
  const r4 = o.nt?.run.call(c, 2);
  const n4: string = r4;
}
