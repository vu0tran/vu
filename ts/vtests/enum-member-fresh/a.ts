// An enum member read as a value is a fresh literal: it widens to its enum (let, arrays, object
// literals, inferred returns), as getDeclaredTypeOfEnum gives members getFreshTypeOfLiteralType.
enum S { A = 'A', B = 'B', C = 'C' }
enum N { X, Y, Z = 10 }
enum One { Only = 'only' }
const enum CE { P = 1, Q = 2 }

let a = S.A;
a = S.B;
const b = S.A;
let b2 = b;
b2 = S.C;
const arr = [S.A, S.B];
arr.push(S.C);
const obj = { k: S.A, n: N.X };
obj.k = S.B;
obj.n = N.Z;
function f() { return S.A; }
let fr = f();
fr = S.B;
function g(): S.A { return S.A; }
const gr: number = g();
const n1: number = a;
const n2: string = N.X;
const n3: number = b;
const n4: string = arr;
let o1 = One.Only;
const n5: number = o1;
let ce = CE.P;
ce = CE.Q;
const n6: string = ce;
declare function id<T>(x: T): T;
const i1 = id(S.A);
const n7: number = i1;
let i2 = id(S.A);
const n8: number = i2;
declare function arrOf<T>(...xs: T[]): T[];
const ao = arrOf(S.A, S.B);
const n9: number = ao;
function sw(x: S) {
  switch (x) {
    case S.A: { const y: number = x; break; }
    case S.B: return 1;
    default: { const z: number = x; }
  }
  if (x === S.C) { const w: number = x; }
  return 0;
}
const rec: Record<S, number> = { [S.A]: 1, [S.B]: 2, [S.C]: 3 };
const rk: number = rec[S.A];
type T1 = S.A | S.B;
const t1: T1 = S.A;
const t2: T1 = S.C;
const tern = Math.random() > 0.5 ? S.A : S.B;
let tern2 = Math.random() > 0.5 ? S.A : S.B;
tern2 = S.C;
const n10: number = tern;
const tup: [S, number] = [S.A, 1];
const tup2 = [S.A, 1] as const;
const n11: number = tup2;
let numlet = N.X;
numlet = 5;
const n12: string = numlet;
const s1: S.A = S.A;
let s2: S = S.A;
