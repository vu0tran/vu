// require of a CommonJS module whose value is module.exports = x: x's widened type
const { loadConfig, list } = require('./lc');
const m = require('./lc');
/** @type {number} */
const a = m;
/** @type {number} */
const b = loadConfig;
/** @type {number} */
const c = list;
