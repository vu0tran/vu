const { isArray } = Array;
const { hasOwn } = Object;
const isObj = (value: unknown): value is Record<string, unknown> => typeof value === 'object' && value !== null;
export function g() {
  const copy = (value: unknown, depth: number): unknown => {
    if (!isObj(value)) return value;
    if (isArray(value)) {
      const result = new Array<unknown>(value.length);
      for (let i = 0; i < value.length; i++) {
        if (hasOwn(value, i)) result[i] = copy(value[i], depth + 1);
      }
      return result;
    }
    return 1;
  };
  return copy;
}
declare const ix: Record<string, unknown> & any[];
export const ix1: 'z' = ix[0 as number];
declare const iy: { [k: string]: string } & { [k: number]: 'a' };
export const iy1: 'z' = iy[1 as number];
export const iy2: 'z' = iy['s' as string];
