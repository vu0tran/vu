declare module "base" {
  namespace base {
    interface Shape { join(a: string, b: string): string }
  }
  const base: base.Shape;
  export = base;
}
declare module "node:base" {
  import base = require("base");
  export = base;
}
declare module "ns" {
  namespace ns { const v: number; }
  export = ns;
}
