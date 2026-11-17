interface Ctx { a: number }
interface Ctx2 extends Ctx { b: string }
interface H {
  req(this: Ctx, opts: { u: string }, n?: number): Promise<number>;
  plain(x: string): number;
}
declare function impl(this: Ctx, o: { u: string }): Promise<number>;
export function make(): H {
  return {
    async req(this, opts, n) {
      const q: string = n;
      return await impl.call(this, opts);
    },
    plain(x) { return x.length; },
  };
}
export function make2(): H {
  return {
    async req(this: Ctx2, opts, n) {
      const q: string = n;
      return 1;
    },
    plain: (x) => x.length,
  };
}
export function g(this, x: number) { return x; }
export const h = function (this, y) { return y; };
