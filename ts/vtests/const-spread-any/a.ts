// a spread of any or an unresolved name's type in a const object literal: the literal is any,
// its other members still checked
import { Addr } from './missing';
declare const raw: Addr;
declare const loose: any;
const o1 = { ...raw, kind: 'a', n: 1 } as const;
const n1: number = o1;
const o2 = { kind: 'b', ...loose, deep: { x: 1 } } as const;
const n2: number = o2;
const o3 = { a: 1, ...{ b: 2 }, c: undefinedName } as const;
const o4 = { ...raw, bad: (1 as string) } as const;
export { n1, n2, o3, o4 };
