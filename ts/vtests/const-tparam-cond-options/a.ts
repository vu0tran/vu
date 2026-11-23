// a const type parameter inside an options parameter whose type is conditional (as Pothos's
// enumType): the options' properties read through its branches; an array whose type can't reach
// the const type parameter isn't in a const context
export {};
type Opts<P, V> = P extends readonly string[] ? { tags?: string[]; values?: V; d: string } : { tags?: string[]; values: V; d: string };
declare function enumType<P, const V extends Record<string, { d?: string }>>(p: P, o: Opts<P, V>): V;
const vals = { A: { d: 'a' } } as const;
const r1 = enumType('x', { d: 'a', tags: ['t'], values: vals });
const n1: number = r1.A.d;
const r2 = enumType('x', { d: 'a', tags: ['t'], values: { B: { d: 'q' } } });
const n2: number = r2.B.d;
