namespace Outer { export interface Opt { a: number } export const v = 1; }
type OuterT = number;
namespace Inner {
  type Outer = string;
  const Outer: number = 1;
  export function f(o: Outer.Opt): Outer { const n: string = o.a; return ""; }
}
namespace Inner2 {
  namespace Outer { export interface Opt { b: string } }
  export function g(o: Outer.Opt) { const n: number = o.b; }
}
export {};
