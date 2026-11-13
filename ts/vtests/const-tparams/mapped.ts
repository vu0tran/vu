type Def = { readonly name: string; readonly props: { kind: 'a' | 'b' } };
type In = { readonly name: string; readonly props: unknown };
function def<const T extends Record<string, In>>(e: T): { readonly [K in keyof T]: T[K] & Def } { return e as never; }
const D = def({ a: { name: 'x', props: { kind: 'a' } }, b: { name: 'y', props: 1 } });
export const n: 'x' = D.a.name;
export const n2: 'z' = D.b.name;
export const k: 'a' = D.a.props.kind;
function track<T extends Def>(d: T, p: T['props']): void {}
// @ts-expect-error bad
track(D.a, { kind: 'c' });
track(D.a, { kind: 'a' });
export const arr = def({ q: { name: 'w', props: [1, 2] } });
export const arr2: readonly [1, 2] = arr.q.props;
