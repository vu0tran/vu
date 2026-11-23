// A rest parameter typed as a conditional type on the type parameters (graphql-request's
// VariablesAndRequestHeadersArgs<V>): the arguments' tuple infers into its branches.
type Variables = object;
type RemoveIndex<T> = { [K in keyof T as string extends K ? never : number extends K ? never : K]: T[K] };
type Args<V extends Variables> = V extends Record<any, never> ? [variables?: V, h?: string] : keyof RemoveIndex<V> extends never ? [variables?: V, h?: string] : [variables: V, h?: string];
declare function request<T = any, V extends Variables = Variables>(doc: string | { t: T; v: V }, ...rest: Args<V>): Promise<V>;
declare const d: any;
export const p: number = request(d, { propertyAddress: { caseId: 'x' } });
declare function req2<V extends Variables = Variables>(...rest: Args<V>): V;
export const q: number = req2({ a: 1 });
export const q2: number = req2();
export const q3: number = req2({ a: 1 }, 'h');
