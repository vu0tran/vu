type R = Partial<{ a: string } & { 'content-type': string }>;
declare class H { [k: string]: any; get(): string }
type AH = R & H;
declare const h: R | AH;
export const z: 'z' = h['content-type'];
declare const h2: { x: number } & { [k: string]: string | number };
export const y: 'z' = h2['qq'];
declare const h3: { x?: number } & { [k: string]: string | number | undefined };
export const w: 'z' = h3['x'];
export const v: 'z' = h3['nope'];
type Q = ({ p: 1 } & { [k: string]: number })['p'];
export const u: 'z' = null as unknown as Q;
