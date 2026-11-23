/**
 * An @ before no name (versions like @^0.37.3, emails like a@b): not tags, nothing typed.
 * @param {string} s
 */
export function f(s) {
  return s.length;
}
const raw = JSON.parse('{}');
export async function g() {
  await f('x');
  return raw.y;
}
