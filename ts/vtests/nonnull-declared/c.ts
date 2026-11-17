interface Ctx { a: number }
interface NT { execute?(this: Ctx): Promise<number> }
declare abstract class Nd { execute(ctx: Ctx, x: string[]): Promise<string>; tag: 1 }
declare function isNd(x: unknown): x is Nd;
export async function f(nt: NT, c: Ctx) {
  if (nt.execute) {
    const d = isNd(nt) ? await nt.execute(c, []) : await nt.execute.call(c);
    const n: boolean = d;
  }
}
