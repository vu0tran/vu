declare const page: object;
declare function ev(...a: unknown[]): any;
let pred: ((xs: string[], s?: string) => unknown) | undefined;
Object.defineProperties(page, {
  waitForFunction: {
    value: async (fn: (...args: string[]) => unknown, ...args: string[]) => {
      pred = (xs, s) => ev(fn, args, xs, s);
    },
  },
});
function g() {
  pred = (xs, s) => ev(xs, s);
}
let r2: (() => string) | undefined;
r2 = () => ev();
class K { static readonly NAMES: string[] = ['a']; static f = () => ev(); }
const SYM = Symbol('x');
const SYM2 = Symbol.for('y');
export { SYM, SYM2, K };
