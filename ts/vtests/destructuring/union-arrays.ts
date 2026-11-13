export {};
declare const g: string[] | undefined;
declare const u: string[] | number[];
const [start] = g ?? [];
const s1: boolean = start;
const [a, ...b] = u;
const s2: boolean = a; const s3: boolean = b;
const [c = 1] = u;
const s4: boolean = c;
