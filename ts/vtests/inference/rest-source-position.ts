interface O { owner: string }
interface D<P extends O, Q = P> { pt: (s: P) => number; dt: (s: Q) => number }
interface R<P extends O, Q = P> { p(s: P): void; d(s: Q): void }
declare function mk<P extends O, Q = P>(d: D<P, Q>): R<P, Q>;
declare const anyfn: (...args: any[]) => any;
const r = mk({ pt: anyfn, dt: anyfn });
const z: 'z' = r;
r.d({ owner: 'a', ref: 'b' });
