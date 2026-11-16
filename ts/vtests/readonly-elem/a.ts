// Writing a read-only property through an element access: TS2540 at the index.
type E = { "A:exit": number; "B:exit": number; "C-d": number };
export const e: E = {};
type F = { "A:exit": number };
export const f: F = {};
interface G { readonly "x-y": number; readonly z: number }
declare const g: G;
g["x-y"] = 1;
g["z"] = 1;
g.z = 2;
