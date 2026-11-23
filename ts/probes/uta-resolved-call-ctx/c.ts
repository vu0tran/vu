declare function useMemo<T>(f: () => T, deps: unknown[]): T;
type Photo = { id: string };
export function f(xs: string[] | undefined) {
  return useMemo(() => {
    if (!xs?.length) return {} as Record<string, Photo[]>;
    const m: Record<string, Photo[]> = {};
    return m;
  }, [xs]);
}
export const g = [1, 2].map((x) => ({ key: String(x) as string | undefined, n: x }));
declare function h(f: () => Array<{ v: unknown }>): void;
h(() => [{ v: undefined as unknown }]);
declare function mut(o: { variables: { t: 'A' | 'B' } }): void;
declare const t0: 'A' | 'B';
mut({ variables: { t: t0 as 'A' | 'B' } });
declare function gmut<V>(o: { variables: V }): void;
gmut<{ t: 'A' | 'B'; u: string }>({ variables: { t: 'A' as 'A' | 'B', u: 'x' as string } });
