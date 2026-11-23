// a rest parameter typed as a tuple whose element is an intersection with a type parameter: each
// argument's contextual type is the element at its position (Hono's get(path, middleware, handler))
type Ctx<P> = { path: P; json(x: object): Response };
type Handler<P, R> = (c: Ctx<P>, next: () => Promise<void>) => R;
type Mw<P> = (c: Ctx<P>, next: () => Promise<void>) => Promise<void>;
type H<P, R = any> = Handler<P, R> | Mw<P>;
declare function get1<P extends string, R = any>(path: P, ...hs: [H<P>, H<P, R>]): R;
declare function get2<P extends string, R = any, M1 extends H<P> = H<P>>(path: P, ...hs: [H<P> & M1, H<P, R>]): R;
declare function get3<P extends string, R = any>(...hs: [H<P>, H<P>, H<P, R>]): R;
declare function get4<P extends string, R = any>(path: P, ...hs: [H<P>, H<P, R>]): R;
declare function get4<P extends string, R = any>(...hs: [H<P>, H<P>, H<P, R>]): R;
declare const mw: Mw<string>;
export const b = get2('/x', mw, async (c) => { const n: number = c; return 1; });
