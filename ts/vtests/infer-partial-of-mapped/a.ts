// Inference to Partial<{ [K in keyof T]: F }>: the outer template X[P] is X's template at P, so T is reverse mapped (substituteIndexedMappedType).
declare function c1<T extends Record<string, unknown> = {}>(o: { server: Partial<{ [K in keyof T]: T[K] }> }): T;
const r1: number = c1({ server: { a: 1, b: "x" } });
declare function c2<T extends Record<string, unknown> = {}>(o: { server: { [K in keyof T]: T[K] } }): T;
const r2: number = c2({ server: { a: 1, b: "x" } });
declare function c3<P extends string | undefined, T extends Record<string, unknown> = {}>(o: { server: { [K in keyof T]: P extends undefined ? T[K] : never } }): T;
const r3: number = c3({ server: { a: 1, b: "x" } });
declare function c4<P extends string | undefined, T extends Record<string, unknown> = {}>(o: { server: Partial<{ [K in keyof T]: P extends undefined ? T[K] : never }> }): T;
const r4: number = c4({ server: { a: 1, b: "x" } });
