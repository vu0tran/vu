declare module "mm" {
  class M { constructor(x: string); go(): void; }
  namespace M { function make(p: string): number; const k: string; }
  export = M;
}
declare module "nn" {
  function f(x: number): string;
  namespace f { const v: boolean; }
  export = f;
}
