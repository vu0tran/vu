// an object without index signatures indexed by string or number while instantiating (a
// declaration file's T[K], skipLibCheck): unknown, getIndexedAccessType without an access node
import type { Idx, NIdx } from './lib';
declare const x: Idx<{ a: 1 }, string>;
const n1: number = x.v;
declare const y: NIdx<{ a: 1 }, number>;
const n2: number = y.v;
