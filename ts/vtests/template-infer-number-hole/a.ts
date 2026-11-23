// (inference to `${N}`, N extends number: a string literal match converted, "3" to 3; a `${number}`
// match inferred as it is, then not fitting the constraint, N is number)
declare function idx<N extends number>(s: `${N}`): N;
declare function idx2<N extends number>(s: `a.${N}.b`): N;
declare const i: number;
const r1 = idx(`${i}`);
const r2 = idx("3");
const r3 = idx2(`a.${i}.b`);
const r4 = idx2("a.7.b");
const s1: string = r1;
const s2: string = r2;
const s3: string = r3;
const s4: string = r4;
export {};
