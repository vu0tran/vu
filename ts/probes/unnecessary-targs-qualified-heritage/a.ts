// a qualified class heritage's type arguments (extends ns.Base<...>)
export namespace ns {
  export class Base<P = {}, S = number> { p?: P; s?: S }
}
export class A extends ns.Base<{ x: 1 }> {}
export class B extends ns.Base<{ x: 1 }, number> {}
export class C extends ns.Base<{}> {}
