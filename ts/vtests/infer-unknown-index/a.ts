// inferring to a type whose alias reads R["$typeName"] of an infer R not yet inferred: that
// indexed access of unknown is unknown, not something the checker can't type
type Message<N extends string = string> = { readonly $typeName: N; $unknown?: unknown[] };
type Names<R extends Message> = Message extends R ? string : Exclude<keyof R, keyof Message>;
type Desc = { kind: 'msg'; name: string; typeName: string; field: Record<string, number> };
type Gen<R extends Message> = Omit<Desc, "field" | "typeName"> & { field: Record<Names<R>, number>; typeName: R["$typeName"] };
type Shape<D> = D extends Gen<infer R> ? R : Message;
type Init<D> = D extends Gen<infer R> ? R | Partial<Omit<R, "$typeName">> : Record<string, unknown>;
declare function create<D extends Desc>(d: D, init?: Init<D>): Shape<D>;
type V = Message<"V"> & { a: number; k: { case: 'x'; value: number } | { case: undefined; value?: undefined } };
declare const VSchema: Gen<V>;
export const v1 = create(VSchema, { a: 1, k: { case: undefined } });
const n1: number = v1;
