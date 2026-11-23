// module as a value in a CommonJS file: the file's own module, { exports: the module's value };
// require.resolve, the global require's
const x = 1;
const p = require.resolve('./m');
module.exports = { x, p };
/** @type {number} */
const r = require.resolve;
if (require.main === module) {
  const m = module;
  /** @type {number} */
  const n = m;
}
