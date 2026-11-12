export namespace NS {
  export type A = { a: number };
  export interface B { b: string }
  type Hidden = 1;
  export namespace Inner { export type C = NS.A & { c: Hidden } }
}
export const x: NS.A = { a: "s" };
export const y: NS.Inner.C = { a: 1, c: 2 };
