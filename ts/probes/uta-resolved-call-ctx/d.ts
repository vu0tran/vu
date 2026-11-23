declare function useMemo<T>(f: () => T, deps: unknown[]): T;
declare function useCb<T extends (...a: never[]) => unknown>(f: T, deps: unknown[]): T;
export function k2<T>(f: () => T | undefined) {
  return useMemo(() => {
    return f() as T;
  }, []);
}
export function k3<T>(x: unknown) {
  const o: { v: T } = { v: x as T };
  return o;
}
export const cb = useCb((x: string) => {
  return { n: x as string | number };
}, []);
export const m2 = useMemo(() => {
  const r = [] as string[];
  return { r, s: 'a' as string };
}, []);
