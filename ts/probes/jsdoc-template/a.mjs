// @template T on a JavaScript function: its type parameters ({C} constraining them)
const raw = JSON.parse('{}');

/** @template Value @param {() => Value | PromiseLike<Value>} operation */
const track = (operation) => {
  return operation();
};
export const n = track(() => 1).toFixed();
export const s = track(() => raw.s);

/**
 * @template {string} K, V
 * @param {K} k
 * @param {V} v
 * @returns {Record<K, V>}
 */
export function one(k, v) {
  return /** @type {Record<K, V>} */ ({ [k]: v });
}
export const o = one('a', raw.x);
export async function f() {
  await one('b', 1).b;
  await track(() => Promise.resolve(2));
}
