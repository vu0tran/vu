// JSDoc types of a JavaScript file (checkJs): @param, @returns, @type, @typedef
import { find, counts, status, named, type Item } from './b.mjs';
const r: number = find([], 1);
const c: string = counts.x;
const s: string = status(1);
const n: number = named('x');
declare const it: Item;
const nm: number = it.name;
find([], 'a');
