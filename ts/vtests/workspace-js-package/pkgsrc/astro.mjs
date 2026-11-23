/**
 * @param {{ base?: string, n?: number }} options
 */
export function cfg({ base = "/", n = 1 }) {
  return { base, n: n + 1 };
}
