// An optional parameter's type has undefined in it when a signature infers from it
// (React's useReducer(reducer, initArg, init) with init(id?: string)).
type Reducer<S, A> = (prevState: S, action: A) => S;
type ReducerState<R extends Reducer<any, any>> = R extends Reducer<infer S, any> ? S : never;
declare function useR4<R extends Reducer<any, any>, I>(
  reducer: R,
  initializerArg: I,
  initializer: (arg: I) => ReducerState<R>,
): [ReducerState<R>, I];
interface St { on: boolean }
declare function init(id?: string): St;
declare function reducer(state: St, action: number): St;
declare const id: string | undefined;
const b = useR4(reducer, id, init);
const n: number = b;

declare function pick<T>(x: T, f: (a: T) => void): T;
declare function opt(a?: number): void;
declare const u: number | undefined;
const p = pick(u, opt);
const m: string = p;
declare function keyed<K>(x: { toFixed(d?: K): string }): K;
const k1: string = keyed(3);
declare function both<K>(f: (a?: K) => void): K;
declare function g2(a?: string): void;
const k2: number = both(g2);
