// a const type parameter's call with an options argument whose parameter type is a union with a
// primitive (zod's z.literal(value, string | params)): the primitive has no properties
export {};
type ErrMap<T> = string | ((issue: T) => string);
interface Params<T> { error?: ErrMap<T>; message?: string }
declare function literal<const T extends string | number | boolean>(value: T, params?: string | Params<T>): { value: T };
const a = literal(true, { error: 'Confirm.' });
const n1: number = a.value;
const b = literal('x', { error: (i) => { const q: boolean = i; return ''; } });
const n2: number = b.value;
