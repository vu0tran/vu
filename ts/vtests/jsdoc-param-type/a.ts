// JSDoc types on parameters (/** @type {T} */ x), constructors and object methods
import { Failure, arrow, rest, obj } from './b.mjs';
new Failure('c');
const a: string = arrow(1);
arrow('1');
const r: string = rest('a', 'b');
const o: number = obj.run((x) => String(x), 1);
obj.size(1);
