// An arrow without parameters returning an object literal with untyped method parameters is
// context-sensitive (hasContextSensitiveReturnExpression): it waits for the other arguments'
// inferences, so React's useImperativeHandle(ref, () => ({ insert(text) {} })) types text.
interface RefObject<T> { current: T | null }
type Ref<T> = RefObject<T> | ((x: T | null) => void) | null;
declare function useImperativeHandle<T, R extends T>(ref: Ref<T> | undefined, init: () => R): void;
interface Handle { insert(text: string): void; sel(s: { anchor: number }): number }
declare const ref: Ref<Handle>;
useImperativeHandle(ref, () => ({
  insert(text) { const n: number = text; },
  sel(s) { return s.anchor; },
}));
declare function f2<T, R extends T>(t: T, init: () => R): R;
f2({ a: (x: string) => {} }, () => ({ a(x) { const m: number = x; } }));
f2({ a: (x: string) => {} }, () => ({ a: (x) => { const m: boolean = x; } }));
declare function f3<T>(init: () => T, t: T): T;
const r3 = f3(() => ({ k: 1 }), { k: 2 });
const n3: string = r3;
declare function f4<T>(init: () => { cb: (x: T) => void }, t: T): T;
f4(() => ({ cb(x) { const q: string = x; } }), 5);
