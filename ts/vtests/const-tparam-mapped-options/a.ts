// a const type parameter inside an options parameter that is a generic mapped type (as Pothos's
// objectType): a property's contextual type is the template for its name; an array literal is in
// a const context only where that type is a const type variable (isConstTypeVariable)
export {};
type Norm<T> = { [K in keyof T]: T[K] };
type Opts<P, I> = Norm<(P extends string ? {} : { name: string }) & { tags?: string[]; interfaces?: I; list?: I[] }>;
declare function obj<const I, P>(p: P, o: Opts<P, I>): I;
const r2 = obj('s', { tags: ['a', 'b'], interfaces: ['q'] });
const n2: number = r2;
const r3 = obj('s', { tags: ['a'], list: ['q'] });
const n3: number = r3;
