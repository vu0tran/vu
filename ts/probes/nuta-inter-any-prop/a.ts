interface PQ { [key: string]: undefined | string | PQ | (string | PQ)[] }
declare const query: PQ;
const w = query['w'];
export const o1: { a: any } & { b?: number } = { a: w as string };
export const o2: { a: any } & { a: any } = { a: w as string };
export const o3: { [k: string]: any } & { b?: number } = { a: w as string };
export const o4: { [k: number]: any } & { [k: string]: any } = { a: w as string };
export const o5: { [k: symbol]: any } & { [k: string]: any } = { a: w as string };
export const o6: { [k: string]: any } & { [k: string]: any } = { a: w as string };
export const o7: { a: any } & { [k: string]: any } = { a: w as string };
export const o8: { [k: string]: any } & {} = { a: w as string };
