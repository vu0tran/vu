declare function useMemo<T>(f: () => T, deps: unknown[]): T;
declare const c: boolean;
export const colors = useMemo(() => {
  if (c) {
    return { bg: 'a', text: 'b' };
  }
  return { bg: 'c', text: 'd', secondaryText: 'e' };
}, []);
const z: number = colors.secondaryText;
declare function id<T>(t: T): T;
export const k = id(c ? { a: 1 } : { a: 2, b: 'x' });
const y: number = k.b;
