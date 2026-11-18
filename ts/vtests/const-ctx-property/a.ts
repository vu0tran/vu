interface Tool { name: string }
interface Params<TT extends readonly Tool[], N extends string> { model: string; tools?: TT; name?: N; nested?: { deep: TT } }
declare function create<const TT extends readonly Tool[] = readonly Tool[], const N extends string = string>(p: Params<TT, N>): { tools: TT; name: N };
declare const t1: Tool;
export const a = create({ model: 'x', tools: [t1, { name: 'q' }], name: 'nm' });
export const n1: number = a;
export const b = create({ model: 'x', nested: { deep: [{ name: 'z' }] } });
export const n2: number = b;
declare function mk<const T extends Tool[]>(p: { list: T; other: number }): T;
export const n3: number = mk({ list: [{ name: 'm' }], other: 1 });
