// a conditional type in a later declaration of a merged interface: the interface's type parameter
// (its first declaration's) is mapped there too
export {};
interface Ext<P extends { Kind?: string; Ctx?: object }> { Ctx: P['Ctx'] & {} }
interface Ext<P extends { Kind?: string; Ctx?: object }> {
  Kind: P['Kind'] extends string ? P['Kind'] : 'Resolve';
  Pick: P extends { Ctx: infer C } ? C : never;
}
interface ST { Ctx: { c: 1 } }
interface ST2 { Kind: 'Other' }
declare const k1: Ext<ST>['Kind'];
const n1: number = k1;
declare const k2: Ext<ST2>['Kind'];
const n2: number = k2;
declare const k3: Ext<ST>['Pick'];
const n3: number = k3;
