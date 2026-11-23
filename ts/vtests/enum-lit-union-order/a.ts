enum T { Z = 'z_val', A = 'q_val', M = 'a_val', K = 'k' }
enum N { Z = 5, A = 1, M = 3 }
enum O { B = 'b', A = 'a' }
declare const x1: T.A | T.Z | T.M;
const y1: null = x1;
declare const x2: N.A | N.Z;
const y2: null = x2;
declare const x3: O.A | T.Z | O.B | T.M;
const y3: null = x3;
const arr = [T.K, T.A, T.Z] as const;
declare const x4: (typeof arr)[number];
const y4: null = x4;
declare const x5: T.A | 'zz' | 'aa' | T.Z;
const y5: null = x5;
