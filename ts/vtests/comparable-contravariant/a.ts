declare class EH<A> { l: Array<(a: A) => void> }
declare class AT<E> { _eH: EH<E>; clone(): AT<E> }
declare class YE<T> { t: T }
declare class YM<T> extends AT<YE<YM<T>>> { m: T }
export function f(y: AT<unknown>, r: YM<unknown>) {
  let cur: AT<unknown> | null = y;
  if (cur === r) return 1;
  const q: AT<unknown> = r;
  return 0;
}
