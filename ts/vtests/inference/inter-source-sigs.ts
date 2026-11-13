type M = { calls: number } & { (...args: any[]): any } & { tag: string };
interface O { owner: string }
declare function mk<P extends O>(d: { pt: (s: P) => number }): P;
declare const m: M;
export const z: 'z' = mk({ pt: m });
type M2 = { calls: number } & { (s: { owner: string; x: 1 }): number };
declare const m2: M2;
export const z2: 'z' = mk({ pt: m2 });
