// A generic function passed where a non-generic signature is expected (rows.map(withDraft)): its type parameters inferred from that signature's parameters (instantiateTypeWithSingleGenericCallSignature).
declare function withDraft<T extends { d: string | null }>(row: T): Omit<T, "d"> & { draft: string | null };
declare const rows: { id: string; d: string | null }[];
const r = rows.map(withDraft);
const n: number = r;
declare function idf<T>(x: T): T;
const r2: number = rows.map(idf);
const r3: number = ["a", "b"].map(String);
declare function pair<A, B>(a: A, b: B): [A, B];
const r4: number = [1, 2].map(pair);
const r5: number = [1, 2].filter(Boolean);
declare function bad<T extends string>(x: T): T;
const r6 = [1, 2].map(bad);
