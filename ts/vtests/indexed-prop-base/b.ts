function g1<F extends { a: { _def: number } }>(s: F, k: keyof F) { const d: string = s[k]._def; }
function g2<F extends { a: { _def: number }, b: { _def: boolean } }>(s: F, k: keyof F) { const d: string = s[k]._def; }
function g3<F extends { a: { _def: number }, b: { x: 1 } }>(s: F, k: keyof F) { const d: string = s[k]._def; }
function g4<F extends { [k: string]: { _def: number } }>(s: F, k: keyof F) { const d: string = s[k]; }
export {};
function g6<F extends { [k: number]: { _def: number } }>(s: F, k: keyof F) { const d: string = s[k]._def; }
