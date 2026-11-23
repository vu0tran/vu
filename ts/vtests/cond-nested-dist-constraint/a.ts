// the constraint of a conditional whose false branch is a conditional distributive over the check
// type under a non-distributive one (DeepPartial<T>): computed with T's constraint, so reading it
// narrowed is checked
type AnyObject = Record<string, unknown>;
type AnyFn = (...args: any) => any;
type IsPureFunction<T> = T extends AnyFn ? (Exclude<keyof T, 'length' | 'name'> extends never ? true : false) : false;
type DeepPartial<T> = T extends Array<infer U>
  ? Array<DeepPartial<U>>
  : IsPureFunction<T> extends true
    ? T
    : T extends object
      ? { [P in keyof T]?: DeepPartial<T[P]> }
      : T;
export const deepMerge = <T extends AnyObject>(target: DeepPartial<T>, source: DeepPartial<T>): DeepPartial<T> => {
  if (!source) {
    return target;
  }
  const n: number = source;
  return source;
};
type Wrap<T> = [T] extends [never] ? never : T extends string ? `s:${T}` : T extends number ? T : { v: T };
export function g<T extends string | number | boolean>(w: Wrap<T>) {
  if (typeof w === 'string') {
    const s: number = w;
    return s;
  }
  const r: string = w;
  return r;
}
