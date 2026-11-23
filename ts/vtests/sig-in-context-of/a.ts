// a generic source signature against a non-generic target: its type parameters inferred from the target's parameters and return type, not erased
declare const g: <T>(x: T) => T;
declare const f: (x: string) => string;
declare const h: (x: string) => number;
const a1 = [f, g];
const n1: number = a1;
const a2 = [h, g];
const n2: number = a2;
declare const k: <T extends string>(x: T) => T[];
declare const l: (x: "a") => string[];
const a3 = [l, k];
const n3: number = a3;
let fv: (x: number) => number = g;
fv = g;
