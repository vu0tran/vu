// A mapped type whose keys are object types, named by an as clause (graphql's KindVisitor)
type N = { kind: 'A'; a: number } | { kind: 'B'; b: string };
type Fn<T> = (node: T) => void;
type EL<T> = { readonly enter?: Fn<T>; readonly leave?: Fn<T> };
type KV = { readonly [T in N as T['kind']]?: Fn<T> | EL<T> };
declare function visit(v: EL<N> | KV): void;
visit({
  A(node) {
    const n: string = node.a;
  },
  B: { enter(node) { const m: number = node.b; } },
});
// (a key named string: an index signature, xstate's IndexByType)
type E = { type: 'a'; x: 1 } | { type: string; y: 2 };
type I = { [K in E as K['type']]: K };
declare const i: I;
const q: number = i.other;
const r: number = i.a.x;
