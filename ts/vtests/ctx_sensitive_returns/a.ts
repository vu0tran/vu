// isContextSensitive: an arrow whose expression body is context-sensitive, a method or function
// expression without an explicit this parameter, a function whose return statement returns a
// context-sensitive expression; and a function property's contextual signature from the generic
// call's return mapper (instantiateContextualType).
interface L { f?(p: { info: string }): void }
interface M { g?(): Promise<L | void> }
interface M2 { g?(): L }
declare function id<T>(value: T): Promise<T>;
declare function id2<T>(value: T): T;
export const A: Promise<M2> = id({ g: () => ({ f({ info }) { const x: number = info; } }) });
export const B: Promise<M2> = id({ g() { return { f({ info }) { const x: number = info; } } } });
export const C: Promise<M> = id({ g: () => id({ f({ info }) { const x: number = info; } }) });
export const D: M = id2({ g: () => id({ f({ info }) { const x: number = info; } }) });
export const E: M2 = id2({ g: () => { return id2({ f({ info }) { const x: number = info; } }) } });
export const F: M2 = id2({ g: function () { return { f({ info }) { const x: number = info; } } } });
interface N { h?(): Promise<M | void> }
export const G: N = { h: () => Promise.resolve({ g: () => Promise.resolve({ f({ info }) { const x: number = info; } }) }) };
interface Plugin<in T> { start?(c: T): Promise<Listener<T> | void> }
interface Listener<T> { exec?(c: T): Promise<Exec<T> | void> }
interface Exec<T> { field?(p: { info: string; ctx: T }): (() => void) | void }
export const P = <T extends { readonly response: string }>(): Plugin<T> => ({
  start: () =>
    Promise.resolve({
      exec: () =>
        Promise.resolve({
          field({ ctx, info }) {
            const x: number = info;
          },
        }),
    }),
});
// (a generic arrow is not context-sensitive: its parameter is implicitly any)
declare function call<T>(f: T): T;
export const H = call(<U>(x) => x);
