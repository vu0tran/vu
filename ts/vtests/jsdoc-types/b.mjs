/** @typedef {{ id: number, name?: string }} Item */

/**
 * Finds an item.
 * @param {Item[]} items the items
 * @param {number} [id] which
 * @returns {Item | undefined}
 */
export function find(items, id) {
  return items.find((x) => x.id === id);
}

/** @type {Record<string, number>} */
export const counts = {};

/** @param {unknown} v @returns {401 | 403 | undefined} */
export function status(v) {
  return v ? 401 : undefined;
}

export const arrow = /** @param {string} s */ (s) => s.length;

/**
 * @param {string} s
 * @deprecated use find
 */
export const named = (s) => s.toUpperCase();
