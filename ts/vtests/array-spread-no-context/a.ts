declare function arr<T>(): T[];
declare const anyv: any;
export const f1: ((x: number) => void)[] = [...[(x) => { void x; }]];
export const a2: string[] = [...arr()];
export const a3: [number, ...string[]] = [1, ...arr()];
export const a6: string[] = [...new Set()];
const w: string[] = [...new Set(anyv)];
export const a7: number = w;
