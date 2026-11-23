// a source tuple with a leading rest element: inferred to [...P, T] and related to [...X[], Y]
type L<T extends readonly unknown[]> = T extends readonly [...infer Rest, infer Last] ? [Rest, Last] : 'no';
export const e: L<[...string[], number]> = 1n;
export const f: L<[1, 2]> = 1n;
type M<T> = T extends readonly [...string[], number] ? 'y' : 'n';
export const a: M<[...string[], number]> = 1n;
export const b: M<[...string[], string]> = 1n;
declare const s: [string, ...number[], boolean];
export const t1: [string, ...(number | boolean)[]] = s;
export const t2: [...unknown[], boolean] = s;
export const t3: typeof s extends [...unknown[], number] ? 1 : 0 = 1n;
