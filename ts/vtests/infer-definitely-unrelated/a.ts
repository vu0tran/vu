declare function mk<T>(x?: Iterable<T>): Set<T>;
interface Box<T> { forEach(cb: (value: T, v2: T) => void): void }
interface Arr<T> { forEach(cb: (value: T, i: number) => void): void }
declare function mkb<T>(): Box<T>;
declare function mkp<T>(): { forEach(cb: (value: T, v2: T) => void): void };
export const b1: string[] = mk();
export const b2: Arr<string> = mkb();
export const b3: Arr<string> = mkp();
const s: Set<string> | string[] = mk();
export const b4: number = s;
interface K1<T> { kind: 'a'; v: T; x: number }
interface K2 { kind: 'b'; v: string; y: number }
declare function mkk<T>(): K1<T>;
export const b5: K2 = mkk();
interface O1<T> { kind?: 'a'; v: T; x: number }
declare function mko<T>(): O1<T>;
export const b6: K2 = mko();
