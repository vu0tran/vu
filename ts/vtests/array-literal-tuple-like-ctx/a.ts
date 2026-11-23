declare const s: string;
declare const o: string[] | undefined;
const a1 = s.match(/x/) ?? [];
const n1: number = a1;
const a2 = o ?? [];
const n2: number = a2;
const a3 = o || [];
const n3: number = a3;
const a4 = s ? [] : o;
const n4: number = a4;
const a5 = (s.match(/x/) ?? []);
const n5: number = a5;
function f() { return s.match(/x/) ?? []; }
const n6: number = f();
