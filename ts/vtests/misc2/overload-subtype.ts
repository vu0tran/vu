type Params = { message?: string; description?: string } | undefined;
declare class Schema { get description(): string | undefined; readonly tag: string }
declare function rec<V extends Schema>(v: V, p?: Params): 'one';
declare function rec<K extends Schema, V extends Schema>(k: K, v: V, p?: Params): 'two';
declare const a: Schema;
export const r1: 'one' = rec(a, a);
export const r2: 'two' = rec(a, { description: 'x' });
declare function g(x: { a?: number }): 1;
declare function g(x: object): 2;
export const g1: 2 = g(new Date());
export const g2: 2 = g({});
export const g3: 2 = g([]);
