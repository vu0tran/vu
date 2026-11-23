// an array literal whose contextual type intersects a type parameter constrained to an array with
// an array type (Pothos's interfaces: Interfaces & ValidateInterfaces<...>[]): the elements'
// contextual type is the index signatures' intersection, the type parameter's through its constraint
export {};
interface Ref { kind: 'ref'; name: string }
declare const ref: Ref;
type Fn = (x: number) => string;
declare function impl<I extends Ref[]>(o: { interfaces: I & { kind: 'ref' }[] }): I;
const r = impl({ interfaces: [ref] });
const n: number = r;
declare function impl2<I extends Fn[]>(o: { fns: I & Fn[] }): I;
const r2 = impl2({ fns: [(x) => { const s: boolean = x; return ''; }] });
