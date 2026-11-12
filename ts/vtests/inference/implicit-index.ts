declare function rec<T>(r: Record<string, T>): T;
export const a1: string = rec({ a: 1, b: 2 });
export const a2: string = rec({ a: 1, b: "x" });
declare const o: { x: boolean; y?: number };
export const a3: string = rec(o);
interface I { p: number }
declare const i: I;
export const a4: string = rec(i);
declare function num<T>(r: { [k: number]: T }): T;
export const a5: string = num({ 0: 1, 1: 2 });
