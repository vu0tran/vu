// An alias that reaches itself through another alias's function type: the function type's
// signature is resolved lazily in tsc (getReturnTypeOfSignature), so neither alias is circular
// (execa's ExecaMethod = ExecaBind & ..., ExecaBind = (options) => ExecaMethod<...>).
type L = K2;
type K2 = () => L;
declare const l: L;
export const n3: number = l;
export const n4: number = l();
declare const k: K2;
export const n6: number = k();
type T<O> = (s: string) => O;
type M1<O> = B1<O> & T<O>;
type B1<O> = (options: O) => M1<O>;
declare const m1: M1<{}>;
export const a1: number = m1;
export const a2: number = m1({});
type J = K & ((s: string) => 1);
type K = () => J;
declare const j: J;
export const b1: number = j;
export const b2: number = j();
type Opt = { shell?: boolean; cwd?: string };
type M<O extends Opt = Opt> = B<O> & T<O>;
type B<O extends Opt> = <N extends Opt = {}>(options: N) => M<O & N>;
declare const m: M<{}>;
export const c1: number = m({ shell: true });
export const c2: number = m({ shell: true })({ cwd: '' })('x');
type F = () => F;
declare const f: F;
export const d1: number = f()();
