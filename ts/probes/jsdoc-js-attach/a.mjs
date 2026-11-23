// JSDoc as TypeScript reads it in JavaScript: a destructured parameter takes the @param at its
// position, a tag naming no parameter types nothing, a type over several lines, a comment on a
// return of a function, and /** @type {T} */ (x) casts
const raw = JSON.parse('{}');

/** @param {{headers: Record<string, string[]>}} options */
export function headers({ headers }) {
  return Object.keys(headers).map((k) => headers[k].length);
}

/** @param {string} nope */
export function unknownTag(x) {
  return x.y;
}

/**
 * @param {{
 *   a: string,
 *   b: number,
 * }} o
 */
export function multi(o) {
  return o.a.length + o.b;
}

export function make() {
  /** @param {{ n: number }} r @returns {Promise<number>} */
  return async function respond(r) {
    await 1;
    return r.n;
  };
}

export const viaCast = /** @type {{ v: string }} */ (raw).v.length;
export const viaCast2 = /** @type {string} */ (
  raw.s
).trim();
