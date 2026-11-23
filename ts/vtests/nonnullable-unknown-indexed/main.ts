// NonNullable<unknown> (unknown & {}) indexed by number while instantiating: unknown
import type { El, El2 } from './lib';
declare const x: El2<unknown, number>;
const n1: number = x.e;
declare const y: El<unknown>;
const n2: number = y.e;
