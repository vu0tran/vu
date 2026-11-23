// An ES module's own require (createRequire's): require('x') an ordinary call, but const x =
// require('x') and const { a } = require('x') aliases of the module; a property named define or
// module isn't CommonJS
const require = (/** @type {string} */ id) => id.length;
/** @type {string} */
const n = require('graphql');
export const config = { define: { x: 1 }, module() {} };
/** @type {number} */
const d = config.define;
const { size } = require('./d.js');
/** @type {string} */
const s2 = size;
const dm = require('./d.js');
/** @type {number} */
const s3 = dm.f();
