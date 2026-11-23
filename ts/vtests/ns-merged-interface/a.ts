// an exported interface declared again in another block of the same namespace (as Pothos's plugins
// augment PothosSchemaTypes in declare global blocks): one interface, with both blocks' members
export {};
declare global {
  namespace NS {
    interface User { Context: object; Extra: string }
    interface Ext<P extends Partial<User>> { Context: P['Context'] & {} }
  }
}
declare global {
  namespace NS {
    interface User { Auth: object }
    interface Ext<P extends Partial<User>> { Auth: P['Auth'] & {}; Same: P }
  }
}
namespace Local {
  export interface I { a: string }
  interface Hidden { h: 1 }
}
namespace Local {
  export interface I { b: number }
  interface Hidden { k: 2 }
  export const hk: Hidden = { k: 2 };
}
interface Ctx { auth: { ok: boolean } }
interface ST { Context: Ctx }
type E = NS.Ext<ST>;
declare const t1: E['Context'];
const n1: number = t1;
declare const t2: E['Auth'];
const n2: number = t2;
declare const t3: E['Same'];
const n3: number = t3;
declare const i: Local.I;
const n4: number = i.a;
const n5: string = i.b;
