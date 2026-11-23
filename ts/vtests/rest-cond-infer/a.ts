// A rest parameter typed as a conditional type of the type parameters: inferred from the tuple of
// the arguments (graphql-request's VariablesAndRequestHeadersArgs<V>).
type Variables = object;
type RemoveIndex<T> = { [K in keyof T as string extends K ? never : number extends K ? never : K]: T[K] };
type Args<V extends Variables> = V extends Record<any, never> ? [variables?: V, h?: number] : keyof RemoveIndex<V> extends never ? [variables?: V, h?: number] : [variables: V, h?: number];
interface Doc<V> { __v?: (v: V) => void; kind: 'Document' }
declare function g<V extends Variables = Variables>(document: string | Doc<V>, ...rest: Args<V>): V;
declare function h<V extends Variables = Variables>(...rest: Args<V>): V;
export const r1: number = g('x', { a: 1 });
export const r2: number = h({ a: 1 });
export const r3: number = h();
export const r4: number = g('x', { a: 'y' }, 2);
declare function p<T extends unknown[]>(...rest: T extends [infer A] ? [A] : T): T;
export const r5: number = p(1);
