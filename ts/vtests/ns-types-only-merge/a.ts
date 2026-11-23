// a namespace of types only isn't instantiated: a const of its name merges with it
declare namespace Cf { interface Env { a: number } }
declare const Cf: Cf.Env;
export const n: string = Cf.a;
declare namespace Vals { const v: number }
