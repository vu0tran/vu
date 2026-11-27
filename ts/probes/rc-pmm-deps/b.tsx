import { useMemo, useCallback } from 'react';
export function Counter({ n }: { n: number }) {
  const list: number[] = [];
  const m = useMemo(() => list.length + n, [list, n]);
  list.push(n);
  return <div>{m}</div>;
}
export function Fine({ items }: { items: string[] }) {
  const sorted = useMemo(() => [...items].sort(), [items]);
  const pick = useCallback((i: number) => sorted[i], [sorted]);
  return <div onClick={() => pick(0)}>{sorted.length}</div>;
}
