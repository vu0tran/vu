declare module "bufx" {
  export type W<T> = T | { valueOf(): T };
  global {
    interface Bx { u: number }
    var Bx: BxCtor;
  }
}
