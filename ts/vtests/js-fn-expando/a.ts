// f.p = v beside a JavaScript function declaration: its expando property
import { wrap } from './b.mjs';
const w = wrap();
const m: string = w.marked;
const n: string = w.count;
const r: string = w('x');
