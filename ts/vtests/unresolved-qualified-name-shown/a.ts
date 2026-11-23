declare namespace ns { type A = 1 }
declare const a: readonly google.maps.X[];
const n1: number = a;
declare const b: ns.B[];
const n2: number = b;
declare const c: { p: Missing.Q<string> };
const n3: number = c;
declare const d: globalThis.Nope[];
const n4: number = d;
