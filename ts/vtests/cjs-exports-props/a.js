// exports in a CommonJS file whose only uses are exports.x = v: the file's exports, not the
// global any (@types/node's var exports)
const n = 1;
const f = () => 'x';
exports.n = n;
exports.f = f;
/** @type {string} */
const s = exports.n;
const t = exports.f().length;
const u = exports.n.foo;
exports.k = 2;
exports.o = { a: 1, b: null };
const w = exports.k.foo;
const z = exports.o.foo;
