// functions contextually typed by an intersection of signatures (union calls combine them)
export {};
declare const v: never[] | string[] | (number | null)[];
const r = v.some((x) => { const q: boolean = x; return typeof x === 'string'; });
declare const f: ((a: string) => void) & ((a: number, b: boolean) => void);
const g: typeof f = (x, y) => { const q: boolean = x; const w: string = y; };
declare const k: ((cb: (n: number) => void) => void) | ((cb: (s: string) => void) => void);
k((v) => { const q: boolean = v; });
