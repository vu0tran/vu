// Lowercase<string & Record<never, never>> (undici-types' HeaderRecord): the mapping of the pattern
// template `${string & Record<never, never>}`, which removes the lowercase literals of a union.
type HeaderNames = 'Accept' | 'Content-Type' | (string & Record<never, never>);
type KnownHeaderValues = { 'content-type': 'a' | 'b' };
type HeaderRecord = {
  [K in HeaderNames | Lowercase<HeaderNames>]?: Lowercase<K> extends keyof KnownHeaderValues
    ? KnownHeaderValues[Lowercase<K>]
    : string;
};
declare const h: HeaderRecord;
const a: number = h['content-type'];
const b: number = h.accept;
const c: number = h['x-foo'];
const d: HeaderRecord = { 'content-type': 'c', foo: 1 };
type L = Lowercase<string & Record<never, never>>;
const e: L = 'ABC';
const f: L = 'abc';
declare const s: string;
const g: L = s;
const k: number = {} as L;
const m: Lowercase<L> = 'abc';
const n: number = h.Accept;
