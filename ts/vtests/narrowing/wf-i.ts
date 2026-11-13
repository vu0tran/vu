const { isArray } = Array;
const isObj = (value: unknown): value is Record<string, unknown> => typeof value === 'object' && value !== null;
export function f(value: unknown) {
  if (!isObj(value)) return value;
  if (isArray(value)) {
    const q: 'z' = value;
    return value.length;
  }
  const r: 'z' = value;
  return 1;
}
