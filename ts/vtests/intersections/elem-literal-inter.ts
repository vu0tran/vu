type R = Partial<{ a: string } & { 'content-type': string }>;
declare class H { [k: string]: any; get(): string }
type AH = R & H;
declare const h: R | AH;
export const z: 'z' = h['content-type'];
declare const h2: { x: number } & { [k: string]: string | number };
export const y: 'z' = h2['qq'];
