// protobuf-es's create() with a schema from a missing module (any): unknown["$typeName"], met while
// instantiating, is unknown (getIndexedAccessType without an access node)
import { Schema } from './missing';
interface Message { $typeName: string }
interface Desc { kind: 'message'; typeName: string }
type Gen<R extends Message> = Omit<Desc, 'typeName'> & { typeName: R["$typeName"]; brand?: R };
type Init<D extends Desc> = D extends Gen<infer R> ? R | { p: R } : Record<string, unknown>;
type Shape<D extends Desc> = D extends Gen<infer R> ? R : Message;
declare function create<D extends Desc>(d: D, init?: Init<D>): Shape<D>;
const m = create(Schema, { a: 1 });
const x: number = m;
type I = Init<any>;
const i: I = 3;
declare const sa: any;
const m2 = create(sa, { a: 1 });
