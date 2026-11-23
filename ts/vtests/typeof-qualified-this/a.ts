// typeof x.method of a method returning a type of this (zod's parse(): output<this>): this is
// x's type, as a property access reads it
export {};
type output<T> = T extends { _o: infer O } ? O : never;
interface Schema<O> { _o: O; parse(data: unknown): output<this> }
declare const schema: Schema<{ config: { a: string; b?: number } }>;
type C = ReturnType<typeof schema.parse>['config'];
declare const c: C;
const n: number = c;
function f(x: ReturnType<typeof schema.parse>['config']) { const m: number = x.a; }
declare const both: Schema<{ q: 1 }> & { extra: true };
const k: number = null as unknown as ReturnType<typeof both.parse>;
