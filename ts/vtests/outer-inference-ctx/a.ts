// an argument that's a generic call takes its contextual type with what the outer call's earlier
// arguments inferred (getInferenceContext's NoDefault clone), so its callback's parameter is typed
interface Schema<O> { _out: O }
type Out<T> = T extends { _out: infer O } ? O : unknown;
interface Tx<I, O> extends Schema<O> { _in: I }
declare function obj<T>(shape: T): Schema<T>;
declare function transform<I, O>(fn: (input: I) => O): Tx<I, O>;
declare function pipe<A extends Schema<unknown>, B extends Tx<Out<A>, unknown>>(a: A, b: B | Tx<Out<A>, unknown>): Schema<Out<B>>;
const s = pipe(obj({ _rails: { message: 'm' } }), transform((env) => env['_rails'].message));
export const n: number = s;
const t = pipe(obj({ x: 1 }), transform((env) => env.x + 1));
export const k: string = t;
