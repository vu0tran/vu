// ns.N.T with ns a namespace import re-exported: the module's exported namespace
import type { namedTypes } from './main';
import type { types } from './rec';
export type H = (a: namedTypes.File, b: types.namedTypes.Identifier) => void;
declare const h: H;
const n: number = h;
declare const f: types.namedTypes.File;
const m: number = f.name;
const q: types.namedTypes.Nope = 1;
