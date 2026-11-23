declare class JSHandle<T = unknown> { _t: T; }
declare class ElementHandle<T extends object = object> extends JSHandle<T> { _e: T; }
type HandleFor<T> = T extends object ? ElementHandle<T> : JSHandle<T>;
type HandleOr<T> = HandleFor<T> | JSHandle<T> | T;
type FlattenHandle<T> = T extends HandleOr<infer U> ? U : never;
type InnerParams<T extends unknown[]> = { [K in keyof T]: FlattenHandle<T[K]> };
type Awaitable<T> = T | PromiseLike<T>;
type EvaluateFunc<T extends unknown[]> = (...params: InnerParams<T>) => Awaitable<unknown>;
declare function evaluate<Params extends unknown[], Func extends EvaluateFunc<Params> = EvaluateFunc<Params>>(pageFunction: Func | string, ...args: Params): Promise<Awaited<ReturnType<Func>>>;

declare const searchTerm: string;
declare const matchTerm: string;
async function f() {
  const r = await evaluate(({ matchTerm: match }) => {
    const n: number = match;
    return true;
  }, { searchTerm, matchTerm });
  const r2 = await evaluate((needle) => {
    const n: number = needle;
    return 1;
  }, "x");
  const q: string = r;
  const q2: string = r2;
}
declare function ev5<P extends unknown[]>(f: (...p: P) => unknown, ...args: P): void;
declare function ev6<P>(f: (p: P) => unknown, a: P): void;
declare function ev7<P extends unknown[]>(f: (...p: P) => unknown, args: P): void;
declare function ev8<P extends unknown[]>(...args: P): P;

ev5((needle) => { const n: number = needle; return 1; }, "x");
ev6((needle) => { const n: number = needle; return 1; }, "x");
ev7((needle) => { const n: number = needle; return 1; }, ["x"]);
const r8: number = ev8("x");
