// a function whose contextual type intersects two function types with large return unions (Pothos's
// resolveType once its type parameter is inferred): the signatures combined, returns intersected
export {};
interface R0 { kR0: 1 }
interface R1 { kR1: 1 }
interface R2 { kR2: 1 }
interface R3 { kR3: 1 }
interface R4 { kR4: 1 }
interface R5 { kR5: 1 }
interface R6 { kR6: 1 }
interface R7 { kR7: 1 }
interface R8 { kR8: 1 }
type Ev = { kind: 'R0' } | { kind: 'R1' } | { kind: 'R2' } | { kind: 'R3' } | { kind: 'R4' } | { kind: 'R5' } | { kind: 'R6' } | { kind: 'R7' } | { kind: 'R8' };
type Ret = R0 | R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8;
type F1 = (e: Ev) => Ret;
type F2 = (e: Ev, n: number) => Ret | string | null | undefined | Promise<Ret | string>;
declare const refs: { [K in Ret extends infer _ ? string : never]: Ret };
const f: F1 & F2 = (e) => { const x: number = e; return null as unknown as R0; };
