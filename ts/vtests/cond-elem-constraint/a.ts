// an element of a conditional type by a string: its constraint's (getReducedApparentType)
type AnyObject = Record<string, unknown>;
type AnyFn = (...args: any) => any;
type IsPureFunction<T> = T extends AnyFn
  ? Exclude<keyof T, 'length' | 'name' | 'arguments' | 'caller' | 'prototype'> extends never
    ? true
    : false
  : false;
type DeepPartial<T> =
  T extends Array<infer U>
    ? Array<DeepPartial<U>>
    : IsPureFunction<T> extends true
      ? T
      : T extends object
        ? { [P in keyof T]?: DeepPartial<T[P]> }
        : T;
export const deepMerge = <T extends AnyObject>(source: DeepPartial<T>, key: string) => {
  const v = source[key];
  const n: number = v;
  return n;
};
