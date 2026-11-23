export {};
// a call in an argument of a generic call: the outer T, not inferred yet, gives nothing to the
// inner call's return-type inference (tsc: silentNever in the contextual type)
type output<T> = T extends { _zod: { output: any } } ? T["_zod"]["output"] : unknown;
interface Internals<out O = unknown, out I = unknown> { output: O; input: I }
interface ZT<O = unknown, I = unknown, N extends Internals<O, I> = Internals<O, I>> {
  _zod: N;
  pipe<T extends ZT<any, output<this>>>(target: T | ZT<any, output<this>>): [this, T];
}
interface DateInternals<T = unknown> extends Internals<Date, T> {}
interface CoercedDate<T = unknown> extends ZT<Date, T, DateInternals<T>> {}
interface Str extends ZT<string, string> {}
declare function date<T = unknown>(): CoercedDate<T>;
declare const s: Str;
const r = s.pipe(date());
const n: number = r;
