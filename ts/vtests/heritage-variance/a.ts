type _W<W = any> = typeof globalThis extends { onmessage: any } ? {} : { zz: W };
interface WS<W> extends _W<W> { getWriter(): WritableStreamDefaultWriter<W> }
declare const ws: WS<Uint8Array>;
export const w2: WS<Uint8Array<ArrayBuffer>> = ws;
interface B1<T> { f: T }
interface D1<T> extends B1<T> { g: number }
declare const d1: D1<'a'>;
export const e1: D1<string> = d1;
declare const d2: D1<string>;
export const e2: D1<'a'> = d2;
interface B2<T> { f(x: T): void }
interface D2<T> extends B2<T> {}
declare const d3: D2<string>;
export const e3: D2<'a'> = d3;
interface B3<T> { f: (x: T) => void }
interface D3<T> extends B3<T> {}
declare const d4: D3<'a'>;
export const e4: D3<string> = d4;
declare const b5: B3<'a'>;
export const e5: B3<string> = b5;
declare const p: Promise<string>;
export const f1: Promise<'a'> = p;
declare const q: PromiseLike<string>;
export const f2: PromiseLike<'a'> = q;
declare const r: Set<string>;
export const f3: Set<'a'> = r;
