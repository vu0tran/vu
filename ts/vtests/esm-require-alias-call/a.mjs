// const x = require('x') with the file's own require: an alias of the module, and the call still
// an ordinary call of that require, checked (its argument)
const require = (/** @type {number} */ id) => id;
const dm = require('./d.js');
/** @type {number} */
const s3 = dm.f();
const { size } = require('./d.js');
/** @type {string} */
const s4 = size;
