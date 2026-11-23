// A union written with an aliased union in it, instantiated: its origin's members are instantiated,
// so the alias stays named in what tsc prints (instantiateType on a union's origin).
type RequestDocument = string | String | { kind: 'Document' };
interface TypedDocumentNode<R, V> { __apiType?: (variables: V) => R; kind: 'Document' }
declare class TypedDocumentString<R, V> extends String { __apiType?: (variables: V) => R }
declare function request<T, V>(document: RequestDocument | TypedDocumentNode<T, V> | TypedDocumentString<T, V>): T;
request<number, { a: string }>(5);
declare function g<V>(d: RequestDocument | TypedDocumentNode<any, V>): V;
g<{ b: number }>(true);
