// a method's contextual type from a property whose type mentions this, through a union context
// (Temporal's interceptors: next: Next<this, 'startUpdate'>, workflow?: Interceptors | Interceptor[])
type AnyFunc = (...args: any[]) => any;
type OmitLast<T> = T extends [...infer REST, any] ? REST : never;
type OmitLastParam<F extends AnyFunc> = (...args: OmitLast<Parameters<F>>) => ReturnType<F>;
type Next<IF, FN extends keyof IF> = Required<IF>[FN] extends AnyFunc ? OmitLastParam<Required<IF>[FN]> : never;
interface I { f?: (x: number, next: Next<this, 'f'>) => Promise<string>; g?: (x: number) => void }
interface Is { other?: number }
export const a: I = { f(x, next) { return next(x); } };
export const b: I[] = [{ f(x, next) { return next(x); } }];
export const c: { w?: Is | I[] } = { w: [{ f(x, next) { return next(x); } }] };
export const e: number = (c.w as I[]).length + "";
