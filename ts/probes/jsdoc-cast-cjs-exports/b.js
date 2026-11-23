// @ts-check
const n = 1;
const inc = (/** @type {number} */ x) => x + 1;
exports.n = /** @type {number} */ (n);
exports.inc = inc;
const r = /** @type {number} */ (exports.inc(exports.n));
