// spreads of intersections: their properties, optional ones printed without undefined
export {};
type E = { a: number; b?: string };
type I = E & { m?: boolean; a: 1 | 2 };
declare const i: I;
declare const iu: I | undefined;
const r1 = { z: 1, ...i }; const k1: number = r1;
const r2 = { ...i, z: 1 }; const k2: number = r2;
const r3 = { z: 1, ...iu }; const k3: number = r3;
const r4 = { z: 1, ...i, y: 2 }; const k4: number = r4;
const r5 = { b: 1, ...i }; const k5: number = r5;
type D = { [key: string]: string | number | undefined };
declare const d: D & { $t?: string; $n: number };
const r6 = { a: 1, ...d }; const k6: number = r6;
const r7 = { ...d }; const k7: number = r7;
