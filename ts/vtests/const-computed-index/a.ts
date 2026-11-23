// a const object literal's key that isn't a literal (an unresolved import's member, any; a string;
// a number): an index signature of the values, widened
import { E } from './missing';
declare const k: string;
declare const n: number;
const a = { [E.A]: 'x', [E.B]: 'y', c: 1 } as const;
const b = { [k]: 'x', [n]: 2, 3: true } as const;
const c = { [n]: 'x', d: 'z' } as const;
const v1: number = a[0];
const v2: number = b.zz;
const v3: number = c[1];
const v4: number = a.c;
const v5: string = c.d;
