// the lib's iterable interfaces print without trailing default arguments; other interfaces keep them
interface Box<T, U = string> { t: T; u: U }
declare const b: Box<1>;
declare const it: Iterable<string>;
declare const ii: IterableIterator<number>;
declare const ai: AsyncIterable<string>;
declare const m: Map<string, number>;
export const x1: string = b;
export const x2: string = it;
export const x3: string = ii;
export const x4: string = ai;
export const x5: string = new Map<string, number>(m);
export const x6: number = m.entries();
