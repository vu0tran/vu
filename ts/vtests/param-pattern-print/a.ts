const f1 = ({ a, b }: { a: number; b: string }) => a;
const f2 = ({
  a,
  b = "x",
}: { a: number; b: string }) => a;
const f3 = ({ a: { c }, ...rest }: { a: { c: number }; d: string }) => c;
const f4 = ([x, , y = 2, ...zs]: number[]) => x;
function f6({ a }: { a: number }, [b]: [string]) { return a; }
const f7 = ({ a: aa = 3, }: { a: number }) => aa;
const f8 = ([
  x,
  y,
]: number[]) => x;
const f9 = ({ a, b }: { a: number; b: string }, { c }: { c: number }) => a;
const f10 = ([, x]: number[]) => x;
const f11 = ([x, ,]: number[]) => x;
const f12 = ({ 1: one, a: [p, q] }: { 1: number; a: number[] }) => one;
const z1: number = f1;
const z2: number = f2;
const z3: number = f3;
const z4: number = f4;
const z6: number = f6;
const z7: number = f7;
const z8: number = f8;
const z9: number = f9;
const z10: number = f10;
const z11: number = f11;
const z12: number = f12;
