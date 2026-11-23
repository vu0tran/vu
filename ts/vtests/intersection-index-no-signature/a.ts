// An intersection indexed by string or number: a primitive member by its apparent type (string & {}
// reads String's number index); none with an index signature for the key: TS7053 for an element
// access, TS2537 written (observability's window[l] under @ts-ignore).
type S = string & {};
const s1: number = null! as S[number];
declare const sx: S;
const s2: number = sx[0];
const w1: number = null! as (Window & typeof globalThis)[string];
declare const k: string;
const w2: number = window[k as any];
