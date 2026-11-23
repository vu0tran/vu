type Opts<V> = {} extends V ? { variables?: V } : { variables: V };
interface Doc<D, V> { __d?: D; __v?: V }
declare function useQ<D, V extends object = {}>(doc: Doc<D, V>, opts?: Opts<NoInfer<V>> & { skip?: boolean }): D;
declare const doc1: Doc<string, { id: number }>;
export const r1: number = useQ(doc1, { variables: { id: 1 } });
useQ(doc1, { variables: { id: "x" } });
declare const doc2: Doc<number, {}>;
export const r2: number = useQ(doc2);
declare function pick<T extends string>(xs: T[], d: NoInfer<T>): T;
export const p1 = pick(["a", "b"], "a");
pick(["a", "b"], "c");
declare function both<T>(a: T, b: { x: NoInfer<T> }): T;
export const b1: string = both(1, { x: 2 });
both("s", { x: 3 });
function inner<T extends { n: number }>(v: NoInfer<T>, w: T) { const k: number = v.n; return [v, w]; }
export { inner };
